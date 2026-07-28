"""
RSS 采集器 - 从多个RSS源获取AI新闻
"""
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from collector.base import BaseCollector, RawItem
from scripts.config import RSS_FEEDS, MAX_ITEMS_PER_SOURCE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# 用于中英文来源检测的通用中文域名/URL模式
CN_PATTERNS = [
    r'\.cn[/?]', r'jiqizhixin', r'qbitai', r'syncedreview',
    r'synced', r'leiphone', r'36kr', r'huxiu', r'geekpark',
    r'chinaventure', r'pedaily',
]


def _is_chinese_source(source_name: str, url: str) -> bool:
    """根据来源名和URL判断是否为中文来源"""
    for pattern in CN_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE) or re.search(pattern, source_name, re.IGNORECASE):
            return True
    return bool(re.search(r'[一-鿿]', source_name))


def _detect_language(text: str) -> str:
    """简单的中英文检测"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    return 'zh' if chinese_chars > 5 else 'en'


def _clean_html(raw: str) -> str:
    """清除HTML标签，保留纯文本"""
    if not raw:
        return ""
    try:
        return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)
    except Exception:
        return re.sub(r'<[^>]+>', '', raw)


def _parse_date(date_str: Optional[str], default: datetime) -> str:
    """解析日期字符串为ISO格式"""
    if not date_str:
        return default.isoformat()
    try:
        # feedparser 返回的可能是时间元组或字符串
        if hasattr(date_str, 'tm_year'):  # time.struct_time
            dt = datetime.fromtimestamp(
                datetime(*(date_str[:6])).timestamp(), tz=timezone.utc
            )
        else:
            dt = date_parser.parse(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return default.isoformat()


class RssFetcher(BaseCollector):
    """RSS 源采集器"""

    def __init__(self):
        super().__init__("RSS Fetcher")

    def _fetch_one_feed(self, source_name: str, feed_url: str) -> list[RawItem]:
        """抓取单个 RSS 源"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=48)  # 只取最近48小时的

        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                logger.warning("[%s] RSS解析异常: %s -> %s", self.name, source_name, feed.bozo_exception)
                return items

            entries = feed.entries[:MAX_ITEMS_PER_SOURCE]
            for entry in entries:
                title = _clean_html(entry.get('title', ''))
                link = entry.get('link', '')
                published = _parse_date(entry.get('published') or entry.get('updated'), now)
                summary = _clean_html(entry.get('summary') or entry.get('description', ''))

                if not title or not link:
                    continue

                # 可选：对中文来源抓取全文
                raw_text = summary
                if _is_chinese_source(source_name, link) and summary and len(summary) < 100:
                    try:
                        full_text = self._fetch_full_text(link)
                        if full_text:
                            raw_text = full_text
                    except Exception:
                        pass

                language = _detect_language(title + ' ' + summary)
                items.append(RawItem(
                    title=title,
                    url=link,
                    source_name=source_name,
                    published_at=published,
                    raw_text=raw_text,
                    language=language,
                ))

            logger.info("[%s] %s: 获取 %d 条", self.name, source_name, len(items))

        except Exception as e:
            logger.error("[%s] %s 抓取失败: %s", self.name, source_name, e)

        return items

    def _fetch_full_text(self, url: str) -> Optional[str]:
        """尝试从文章页面抓取全文"""
        try:
            resp = self._get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 移除脚本和样式
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            # 尝试常见文章内容选择器
            for selector in ['article', '.article-content', '.post-content', '.entry-content', 'main', '#content']:
                content = soup.select_one(selector)
                if content:
                    text = content.get_text(separator=' ', strip=True)
                    if len(text) > 200:
                        return text
            body = soup.find('body')
            if body:
                return body.get_text(separator=' ', strip=True)[:3000]
        except Exception:
            pass
        return None

    def fetch(self) -> list[RawItem]:
        """抓取所有配置的 RSS 源"""
        all_items: list[RawItem] = []
        for source_name, feed_url in RSS_FEEDS.items():
            items = self._fetch_one_feed(source_name, feed_url)
            all_items.extend(items)
        logger.info("[%s] 总计: %d 条 (来自 %d 个源)", self.name, len(all_items), len(RSS_FEEDS))
        return all_items
