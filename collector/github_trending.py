"""
GitHub Trending 采集器 - 获取热门AI相关仓库
"""
import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from collector.base import BaseCollector, RawItem
from scripts.config import (
    GITHUB_TRENDING_URL, GITHUB_AI_LANGUAGES, GITHUB_AI_KEYWORDS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _matches_ai_keywords(text: str) -> bool:
    """检查文本是否包含AI相关关键词"""
    if not text:
        return False
    text_lower = text.lower()
    for keyword in GITHUB_AI_KEYWORDS:
        # 使用单词边界匹配避免 "train" 匹配 "training" 不够准确的问题
        # 这里用于简单过滤，允许子串匹配
        if keyword in text_lower:
            return True
    return False


class GitHubTrendingFetcher(BaseCollector):
    """GitHub Trending AI 仓库采集器"""

    def __init__(self):
        super().__init__("GitHub Trending")

    def _parse_repo_card(self, article) -> dict | None:
        """解析单个仓库卡片"""
        try:
            # 仓库名
            h2 = article.find('h2')
            if not h2:
                return None
            name_link = h2.find('a')
            if not name_link:
                return None
            repo_name = name_link.get('href', '').strip().lstrip('/')
            # 去除多余空白
            full_text = name_link.get_text(separator=' ', strip=True)
            full_text = re.sub(r'\s+', ' ', full_text)

            # 描述
            desc_p = article.find('p')
            description = desc_p.get_text(separator=' ', strip=True) if desc_p else ''
            description = re.sub(r'\s+', ' ', description)

            # 编程语言
            lang_span = article.find('span', itemprop='programmingLanguage')
            language = lang_span.get_text(strip=True) if lang_span else 'Unknown'

            # 星数
            stars = 0
            star_link = article.find('a', href=re.compile(r'/stargazers'))
            if star_link:
                star_text = star_link.get_text(strip=True)
                star_match = re.search(r'[\d,]+', star_text)
                if star_match:
                    stars_str = star_match.group().replace(',', '')
                    stars = int(stars_str)

            return {
                'repo_name': repo_name,
                'description': description,
                'language': language,
                'stars': stars,
            }
        except Exception:
            return None

    def fetch(self) -> list[RawItem]:
        """抓取 GitHub Trending 页面并过滤AI相关仓库"""
        items: list[RawItem] = []
        now = datetime.now(timezone.utc)

        try:
            resp = self._get(GITHUB_TRENDING_URL, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 查找仓库卡片
            articles = soup.find_all('article', class_='Box-row')
            if not articles:
                # 备用选择器
                articles = soup.select('.Box-row')

            logger.info("[%s] 找到 %d 个trending仓库", self.name, len(articles))

            for article in articles:
                info = self._parse_repo_card(article)
                if info is None:
                    continue

                # 语言过滤
                if info['language'].lower() not in [l.lower() for l in GITHUB_AI_LANGUAGES]:
                    continue

                # 关键词过滤：在描述和仓库名中搜索
                search_text = f"{info['repo_name']} {info['description']}"
                if not _matches_ai_keywords(search_text):
                    continue

                items.append(RawItem(
                    title=f"{info['repo_name']} ({info['language']}, ★{info['stars']:,})",
                    url=f"https://github.com/{info['repo_name']}",
                    source_name="GitHub Trending",
                    published_at=now.isoformat(),
                    raw_text=info['description'],
                    language="en",
                ))

        except Exception as e:
            logger.error("[%s] 抓取失败: %s", self.name, e)

        logger.info("[%s] 过滤后获得 %d 个AI仓库", self.name, len(items))
        return items
