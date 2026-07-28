"""
Product Hunt 采集器 - 获取热门AI产品发布
"""
import logging
import re
from datetime import datetime, timezone, date

from bs4 import BeautifulSoup

from collector.base import BaseCollector, RawItem
from scripts.config import PH_AI_TOPIC_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class ProductHuntFetcher(BaseCollector):
    """Product Hunt AI 产品采集器"""

    def __init__(self):
        super().__init__("Product Hunt")

    def fetch(self) -> list[RawItem]:
        """抓取 Product Hunt AI 话题页面的最新产品"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)
        today = date.today()

        try:
            resp = self._get(PH_AI_TOPIC_URL, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Product Hunt 的产品卡片有多种可能的class名
            product_selectors = [
                '[data-test="post-item"]',
                '.styles_post__',
                '[class*="postItem"]',
                'div[class*="item"]',
            ]

            products = []
            for selector in product_selectors:
                products = soup.select(selector)
                if products:
                    break

            # 如果上面的选择器都不匹配，尝试更通用的方式
            if not products:
                products = soup.select('a[href^="/posts/"]')
                # 去重，获取父级产品卡片
                products = list({p.find_parent('div', class_=re.compile(r'post|item|product')) or p.parent for p in products})

            logger.info("[%s] 找到 %d 个产品元素", self.name, len(products))

            for product in products[:20]:
                try:
                    # 提取产品名
                    name_el = (
                        product.select_one('[class*="name"]') or
                        product.select_one('h3') or
                        product.select_one('h2') or
                        product.select_one('strong')
                    )
                    name = name_el.get_text(strip=True) if name_el else ''

                    # 提取描述
                    desc_el = (
                        product.select_one('[class*="tagline"]') or
                        product.select_one('[class*="description"]') or
                        product.find('p')
                    )
                    description = desc_el.get_text(strip=True) if desc_el else ''

                    # 提取链接
                    link = ''
                    link_el = product.find('a', href=re.compile(r'/posts/'))
                    if link_el:
                        href = link_el.get('href', '')
                        link = f"https://producthunt.com{href}" if href.startswith('/') else href

                    # 提取点赞数
                    votes = 0
                    vote_el = product.select_one('[class*="vote"]') or \
                              product.find(string=re.compile(r'\d+\s*(upvotes|votes|👍)'))
                    if vote_el:
                        try:
                            vote_text = vote_el if isinstance(vote_el, str) else vote_el.get_text(strip=True)
                            vote_match = re.search(r'\d+', vote_text)
                            if vote_match:
                                votes = int(vote_match.group())
                        except (ValueError, AttributeError):
                            pass

                    if name:
                        title = f"🚀 {name}"
                        if votes > 0:
                            title += f" (👍{votes})"
                        items.append(RawItem(
                            title=title,
                            url=link or PH_AI_TOPIC_URL,
                            source_name="Product Hunt",
                            published_at=now.isoformat(),
                            raw_text=description,
                            language="en",
                        ))

                except Exception as e:
                    logger.debug("[%s] 解析产品卡片失败: %s", self.name, e)
                    continue

        except Exception as e:
            logger.error("[%s] 抓取失败: %s", self.name, e)

        logger.info("[%s] 获取 %d 个AI产品", self.name, len(items))
        return items
