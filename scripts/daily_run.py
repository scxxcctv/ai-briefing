#!/usr/bin/env python3
"""
每日运行脚本 - 主编排器
采集 → 去重 → 分批处理 → 聚合 → 保存 → 复制到web目录

用法:
    python scripts/daily_run.py              # 处理今天的新闻
    python scripts/daily_run.py 2026-07-27   # 处理指定日期
"""
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

from collector.rss_fetcher import RssFetcher
from collector.arxiv_fetcher import ArxivFetcher
from collector.github_trending import GitHubTrendingFetcher
from collector.huggingface import HuggingFaceFetcher
from collector.producthunt import ProductHuntFetcher
from processor.deduplicator import deduplicate
from processor.summarizer import Summarizer
from processor.aggregator import aggregate, _chunk_list
from scripts.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, BATCH_SIZE,
    RAW_DIR, BRIEFINGS_DIR, WEB_BRIEFINGS_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("daily_run")


def load_env():
    """加载 .env 文件"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val


def save_json(data, filepath):
    """保存JSON文件，确保中文正常显示"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_collectors() -> list:
    """并发运行所有采集器"""
    collectors = [
        RssFetcher(),
        ArxivFetcher(),
        GitHubTrendingFetcher(),
        HuggingFaceFetcher(),
        ProductHuntFetcher(),
    ]

    all_raw_items = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(c._safe_fetch): c for c in collectors}
        for future in as_completed(futures):
            collector = futures[future]
            try:
                items = future.result()
                all_raw_items.extend(items)
            except Exception as e:
                logger.error("采集器 %s 异常: %s", collector.name, e)
            finally:
                collector.close()

    return all_raw_items


def main(target_date: str | None = None):
    """主编排流程"""
    load_env()

    api_key = os.getenv("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY)
    model = os.getenv("DEEPSEEK_MODEL", DEEPSEEK_MODEL)
    base_url = os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)

    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        logger.error("未设置 DEEPSEEK_API_KEY，请编辑 .env 文件或设置环境变量")
        sys.exit(1)

    if target_date is None:
        beijing_tz = timezone(timedelta(hours=8))
        target_date = datetime.now(beijing_tz).strftime("%Y-%m-%d")

    logger.info("=" * 60)
    logger.info("AI Daily Briefing - %s", target_date)
    logger.info("=" * 60)
    start_time = time.time()

    # ── 第1步：采集 ──────────────────────────────────────
    logger.info("[1/6] Starting collection...")
    raw_items = run_collectors()
    logger.info("[1/6] Collected %d raw items", len(raw_items))

    raw_path = RAW_DIR / f"{target_date}.json"
    save_json(raw_items, raw_path)
    logger.info("Raw data saved: %s", raw_path)

    # ── 第2步：去重 ──────────────────────────────────────
    logger.info("[2/6] Deduplicating...")
    deduped_items = deduplicate(raw_items)
    logger.info("[2/6] Dedup: %d -> %d items", len(raw_items), len(deduped_items))

    if not deduped_items:
        logger.warning("No items after dedup, generating empty briefing...")
        from processor.schema import empty_briefing
        briefing = empty_briefing(target_date)
        save_json(briefing, BRIEFINGS_DIR / f"{target_date}.json")
        save_json(briefing, WEB_BRIEFINGS_DIR / f"{target_date}.json")
        return

    # ── 第3步：分批 ──────────────────────────────────────
    logger.info("[3/6] Batching (%d items/batch)...", BATCH_SIZE)
    batches = _chunk_list(deduped_items, BATCH_SIZE)
    logger.info("[3/6] %d batch(es)", len(batches))

    # ── 第4步：DeepSeek API 处理 ───────────────────────────
    logger.info("[4/6] Processing with DeepSeek API...")
    summarizer = Summarizer(api_key=api_key, model=model, base_url=base_url)
    batch_results = []

    for i, batch in enumerate(batches):
        logger.info("  Batch %d/%d (%d items)...", i + 1, len(batches), len(batch))
        result = summarizer.process_batch(batch, retry=True)
        if result:
            batch_results.append(result)
        else:
            logger.warning("  Batch %d failed, skipped", i + 1)
        if i < len(batches) - 1:
            time.sleep(1.5)

    logger.info("[4/6] API processing done:")
    logger.info("  Success batches: %d/%d", len(batch_results), len(batches))
    logger.info("  Prompt tokens: %d", summarizer.total_input_tokens)
    logger.info("  Completion tokens: %d", summarizer.total_output_tokens)
    logger.info("  Est. cost: $%.4f", summarizer.estimate_cost())

    # ── 第5步：聚合 ──────────────────────────────────────
    logger.info("[5/6] Generating briefing...")
    client = OpenAI(api_key=api_key, base_url=base_url)
    briefing = aggregate(batch_results, target_date, client=client, model=model)

    briefing['stats']['total_collected_raw'] = len(raw_items)
    briefing['stats']['total_after_dedup'] = len(deduped_items)
    briefing['stats']['sources_count'] = len(set(
        item.get('source_name', '') for item in raw_items
    ))
    briefing['stats']['api_tokens_input'] = summarizer.total_input_tokens
    briefing['stats']['api_tokens_output'] = summarizer.total_output_tokens
    briefing['stats']['api_cost_estimate_usd'] = summarizer.estimate_cost()

    # ── 第6步：保存 ──────────────────────────────────────
    logger.info("[6/6] Saving...")
    briefing_path = BRIEFINGS_DIR / f"{target_date}.json"
    web_path = WEB_BRIEFINGS_DIR / f"{target_date}.json"
    save_json(dict(briefing), briefing_path)
    save_json(dict(briefing), web_path)
    logger.info("Saved:")
    logger.info("  %s", briefing_path)
    logger.info("  %s", web_path)

    _cleanup_old_raw_data(target_date)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Done! Elapsed %.1f sec", elapsed)
    logger.info("Summary:")
    logger.info("  Date: %s", target_date)
    logger.info("  Model: %s", model)
    logger.info("  Sources: %d", briefing['stats']['sources_count'])
    logger.info("  Raw: %d", briefing['stats']['total_collected_raw'])
    logger.info("  After dedup: %d", briefing['stats']['total_after_dedup'])
    logger.info("  Published: %d", briefing['stats']['total_published'])
    logger.info("  Categories: %s", ", ".join(
        f"{cat}({stat['count']})"
        for cat, stat in sorted(briefing['categories'].items(), key=lambda x: -x[1]['count'])
        if stat['count'] > 0
    ))
    logger.info("  Cost: $%.4f", briefing['stats']['api_cost_estimate_usd'])
    logger.info("=" * 60)


def _cleanup_old_raw_data(current_date_str: str):
    """清理过期的原始数据文件"""
    from scripts.config import RAW_DATA_RETENTION_DAYS
    try:
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        cutoff = current_date - timedelta(days=RAW_DATA_RETENTION_DAYS)

        for f in RAW_DIR.glob("*.json"):
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d").date()
                if file_date < cutoff:
                    f.unlink()
                    logger.info("Cleaned up: %s", f.name)
            except ValueError:
                pass
    except Exception as e:
        logger.warning("Cleanup error: %s", e)


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(date_arg)
