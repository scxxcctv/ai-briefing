"""
去重器 - 标题模糊匹配去重 + URL精确去重
"""
import logging
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse, urlunparse

from collector.base import RawItem
from scripts.config import DEDUP_TITLE_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    """规范化URL：去除尾部斜杠、协议小写、去除fragment"""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower().lstrip('www.'),
        parsed.path.rstrip('/') or '/',
        parsed.params,
        parsed.query,
        '',  # fragment 去除
    ))
    return normalized


def _normalize_title(title: str) -> str:
    """规范化标题：小写、去标点、去多余空白"""
    title = title.lower().strip()
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def _title_similarity(a: str, b: str) -> float:
    """计算两个标题的相似度（0-1）"""
    return SequenceMatcher(None, _normalize_title(a), _normalize_title(b)).ratio()


def deduplicate(items: list[RawItem], threshold: float = DEDUP_TITLE_SIMILARITY_THRESHOLD) -> list[RawItem]:
    """
    对采集条目进行去重：
    1. 完全相同的URL → 保留第一个
    2. 标题相似度 > threshold → 保留文本更长的
    """
    if not items:
        return []

    result: list[RawItem] = []
    seen_urls: set[str] = set()

    for item in items:
        url = _normalize_url(item.get('url', ''))
        if url and url in seen_urls:
            continue

        # 标题模糊匹配
        is_dup = False
        item_title = item.get('title', '')
        for i, existing in enumerate(result):
            existing_title = existing.get('title', '')
            if _title_similarity(item_title, existing_title) >= threshold:
                is_dup = True
                # 保留原始文本更长的（信息更多）
                if len(item.get('raw_text', '')) > len(existing.get('raw_text', '')):
                    result[i] = item
                break

        if not is_dup:
            result.append(item)
            if url:
                seen_urls.add(url)

    removed = len(items) - len(result)
    if removed > 0:
        logger.info("去重: %d 条 → %d 条 (移除 %d 条重复)", len(items), len(result), removed)

    return result
