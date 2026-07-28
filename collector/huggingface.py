"""
HuggingFace 采集器 - 获取每日论文和趋势模型
"""
import json
import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from collector.base import BaseCollector, RawItem
from scripts.config import (
    HF_PAPERS_URL, HF_MODELS_URL, HF_MAX_MODELS, REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


class HuggingFaceFetcher(BaseCollector):
    """HuggingFace 每日论文和趋势模型采集器"""

    def __init__(self):
        super().__init__("HuggingFace")

    def _fetch_papers(self) -> list[RawItem]:
        """抓取 HF Daily Papers"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)

        try:
            resp = self._get(HF_PAPERS_URL, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # HF papers 页面使用 Next.js，页面数据可能在 __NEXT_DATA__ 或内联在 paper 卡片中
            # 首先尝试从 __NEXT_DATA__ 中提取
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    # 遍历 props 寻找论文数据
                    paper_items = self._extract_papers_from_next_data(data)
                    if paper_items:
                        items.extend(paper_items)
                        logger.info("[%s] 从 __NEXT_DATA__ 解析到 %d 篇论文", self.name, len(paper_items))
                        return items
                except (json.JSONDecodeError, KeyError):
                    pass

            # 备用：直接解析 HTML 中的论文卡片
            paper_cards = soup.select('article[data-target="DailyPaperPaper"]') or \
                          soup.select('.paper-card') or \
                          soup.select('[class*="paper"]')

            for card in paper_cards[:20]:
                title_el = card.find(['h3', 'h4']) or card.select_one('[class*="title"]')
                link_el = card.find('a', href=re.compile(r'/papers/'))
                desc_el = card.select_one('[class*="abstract"]') or card.find('p')

                title = title_el.get_text(strip=True) if title_el else ''
                if not title:
                    continue

                url = ""
                if link_el:
                    href = link_el.get('href', '')
                    url = f"https://huggingface.co{href}" if href.startswith('/') else href

                desc = desc_el.get_text(strip=True) if desc_el else ''
                items.append(RawItem(
                    title=title,
                    url=url,
                    source_name="HuggingFace Papers",
                    published_at=now.isoformat(),
                    raw_text=desc,
                    language="en",
                ))

        except Exception as e:
            logger.error("[%s] 论文抓取失败: %s", self.name, e)

        return items

    def _extract_papers_from_next_data(self, data: dict) -> list[RawItem]:
        """从 __NEXT_DATA__ JSON 中提取论文数据"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)

        def search(obj, depth=0):
            if depth > 10:
                return
            if isinstance(obj, dict):
                # 寻找包含 title 和 paper 的字典
                if 'title' in obj and isinstance(obj.get('title'), str):
                    url = ''
                    if 'id' in obj and isinstance(obj['id'], str):
                        url = f"https://huggingface.co/papers/{obj['id']}"
                    elif 'paper' in obj and isinstance(obj['paper'], dict):
                        url = obj['paper'].get('arxivId', '')
                    items.append(RawItem(
                        title=str(obj['title']),
                        url=url,
                        source_name="HuggingFace Papers",
                        published_at=now.isoformat(),
                        raw_text=str(obj.get('summary', obj.get('abstract', ''))),
                        language="en",
                    ))
                for v in obj.values():
                    search(v, depth + 1)
            elif isinstance(obj, list):
                for v in obj[:50]:  # 限制搜索范围
                    search(v, depth + 1)

        try:
            search(data)
        except Exception:
            pass
        return items

    def _fetch_trending_models(self) -> list[RawItem]:
        """抓取 HF Trending Models"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)

        try:
            resp = self._get(HF_MODELS_URL, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 查找模型卡片
            model_cards = soup.select('article') or soup.select('[class*="model"]')
            count = 0
            for card in model_cards:
                if count >= HF_MAX_MODELS:
                    break

                link = card.find('a', href=re.compile(r'^/[^/]+/[^/]+'))
                if not link:
                    continue

                name_text = link.get_text(strip=True)
                href = link.get('href', '')
                if not name_text or '/' not in href.lstrip('/'):
                    continue

                # 找描述
                desc_el = card.find('p') or card.select_one('[class*="desc"]')
                desc = desc_el.get_text(strip=True) if desc_el else ''

                url = f"https://huggingface.co{href}" if href.startswith('/') else href
                items.append(RawItem(
                    title=f"🤗 {name_text}",
                    url=url,
                    source_name="HuggingFace Models",
                    published_at=now.isoformat(),
                    raw_text=desc,
                    language="en",
                ))
                count += 1

        except Exception as e:
            logger.error("[%s] 模型列表抓取失败: %s", self.name, e)

        return items

    def fetch(self) -> list[RawItem]:
        """采集 HF 论文和趋势模型"""
        all_items: list[RawItem] = []
        all_items.extend(self._fetch_papers())
        all_items.extend(self._fetch_trending_models())
        logger.info("[%s] 总计: %d 条", self.name, len(all_items))
        return all_items
