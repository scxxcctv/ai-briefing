"""
ArXiv 采集器 - 获取最新AI相关论文
"""
import logging
from datetime import datetime, timezone, timedelta

import arxiv

from collector.base import BaseCollector, RawItem
from scripts.config import ARXIV_CATEGORIES, ARXIV_MAX_RESULTS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class ArxivFetcher(BaseCollector):
    """ArXiv AI 论文采集器"""

    def __init__(self):
        super().__init__("ArXiv Fetcher")

    def fetch(self) -> list[RawItem]:
        """搜索最近的AI领域论文"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=48)

        # 构建查询：指定分类
        category_query = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)

        try:
            client = arxiv.Client(
                page_size=ARXIV_MAX_RESULTS,
                delay_seconds=2.0,       # 遵守速率限制
                num_retries=3,
            )

            search = arxiv.Search(
                query=category_query,
                max_results=ARXIV_MAX_RESULTS,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )

            results = list(client.results(search))
            logger.info("[%s] 搜索返回 %d 篇论文", self.name, len(results))

            for paper in results:
                # 筛选近期的论文
                published = paper.published.replace(tzinfo=timezone.utc)
                if published < cutoff:
                    continue

                # 摘要文本
                summary = (paper.summary or "").replace('\n', ' ').strip()

                # 分类标签
                categories = [c for c in paper.categories if any(c.startswith(cat) for cat in ARXIV_CATEGORIES)]

                items.append(RawItem(
                    title=paper.title or "Untitled",
                    url=paper.entry_id or paper.pdf_url or "",
                    source_name=f"ArXiv ({', '.join(categories[:2])})",
                    published_at=published.isoformat(),
                    raw_text=summary,
                    language="en",
                ))

        except Exception as e:
            logger.error("[%s] 搜索失败: %s", self.name, e)

        logger.info("[%s] 获取 %d 篇近期论文", self.name, len(items))
        return items
