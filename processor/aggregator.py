"""
聚合器 - 合并处理结果，生成每日简报总摘要和统计数据
"""
import logging
import time

from openai import OpenAI

from processor.schema import (
    SummarizedItem, DailyBriefing, CategoryStat, BriefingStats, empty_briefing,
)
from scripts.config import CATEGORIES

logger = logging.getLogger(__name__)

# 生成简报总摘要的系统提示
BRIEFING_SUMMARY_PROMPT = """你是一位资深的AI行业分析师。根据以下今日AI新闻条目的标题和分类，撰写一段200-300字的中文简报综述。

要求：
1. 使用"今日AI领域动态"作为开头
2. 按重要性从高到低，自然过渡各个板块
3. 突出最重要的3-5条新闻
4. 语言流畅、信息密集、专业但不枯燥
5. 不需要标题，直接输出正文段落

以下是今日条目：
{items_text}

请直接输出200-300字的简报综述："""


def _chunk_list(lst: list, chunk_size: int) -> list[list]:
    """将列表切分为等大小的块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def aggregate(
    batch_results: list[list[SummarizedItem]],
    date: str,
    client: OpenAI | None = None,
    model: str = "deepseek-chat",
) -> DailyBriefing:
    """
    合并所有批次的处理结果，生成最终简报。
    如果提供 OpenAI client，会调用 API 生成总简报摘要。
    """
    all_items: list[SummarizedItem] = []
    for batch in batch_results:
        all_items.extend(batch)

    if not all_items:
        logger.warning("没有条目可聚合，返回空简报")
        return empty_briefing(date)

    # 构建分类统计
    categories: dict[str, CategoryStat] = {}
    for cat_name in CATEGORIES:
        cat_items = [item['id'] for item in all_items if item.get('category') == cat_name]
        categories[cat_name] = CategoryStat(
            count=len(cat_items),
            items=cat_items,
        )

    # 未分类的放入"应用产品"
    cat_ids = set()
    for cat_items in categories.values():
        cat_ids.update(cat_items['items'])
    uncategorized = [item for item in all_items if item['id'] not in cat_ids]
    if uncategorized:
        for item in uncategorized:
            item['category'] = '应用产品'
        categories['应用产品']['count'] += len(uncategorized)
        categories['应用产品']['items'].extend([item['id'] for item in uncategorized])

    # 生成简报总摘要
    briefing_summary = ""
    if client:
        briefing_summary = _generate_briefing_summary(client, model, all_items)

    # 计算统计
    stats = BriefingStats(
        sources_count=len(set(item.get('source_name', '') for item in all_items)),
        total_collected_raw=0,
        total_after_dedup=0,
        total_published=len(all_items),
        api_tokens_input=0,
        api_tokens_output=0,
        api_cost_estimate_usd=0.0,
    )

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    briefing = DailyBriefing(
        date=date,
        generated_at=now_iso,
        model=model,
        briefing_summary=briefing_summary or _fallback_summary(all_items),
        total_items=len(all_items),
        categories=categories,
        items=all_items,
        stats=stats,
    )

    logger.info("聚合完成: %d 条条目, %d 个分类", len(all_items), len(categories))
    return briefing


def _generate_briefing_summary(
    client: OpenAI,
    model: str,
    items: list[SummarizedItem],
) -> str:
    """调用 DeepSeek API 生成简报总摘要"""
    items_text_parts = []
    for item in sorted(items, key=lambda x: -x.get('importance', 0)):
        parts = [
            f"[{item.get('category', '')}] {item.get('title_zh', '')}",
            f"  重要性: {'★' * item.get('importance', 3)}",
            f"  来源: {item.get('source_name', '')}",
        ]
        items_text_parts.append("\n".join(parts))

    items_text = "\n".join(items_text_parts[:30])

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=600,
            temperature=0.5,
            messages=[
                {"role": "system", "content": "你是一位资深的AI行业分析师，擅长撰写简洁有力的行业综述。"},
                {"role": "user", "content": BRIEFING_SUMMARY_PROMPT.format(items_text=items_text)},
            ],
        )

        return (response.choices[0].message.content or "").strip()

    except Exception as e:
        logger.error("生成简报摘要失败: %s", e)
        return ""


def _fallback_summary(items: list[SummarizedItem]) -> str:
    """当 API 不可用时，基于统计生成简单摘要"""
    if not items:
        return "今日暂无AI领域重要动态。"
    top = sorted(items, key=lambda x: -x.get('importance', 0))[:5]
    top_titles = "、".join(item.get('title_zh', '') for item in top)
    return (
        f"今日AI领域共收录 {len(items)} 条动态。"
        f"重点关注：{top_titles}等。"
        f"涵盖模型发布、应用产品、研究前沿等多个板块。"
    )
