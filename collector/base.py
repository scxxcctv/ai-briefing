"""
采集器基类 - 提供会话管理、UA轮换、重试、safe_fetch等通用能力
"""
import logging
import random
import time
from typing import TypedDict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scripts.config import (
    USER_AGENTS, REQUEST_TIMEOUT, RETRY_COUNT, RETRY_BACKOFF_FACTOR,
)

logger = logging.getLogger(__name__)


class RawItem(TypedDict):
    """原始采集条目的标准格式"""
    title: str
    url: str
    source_name: str
    published_at: str          # ISO格式日期字符串
    raw_text: str              # 原始文本（摘要或全文）
    language: str              # 'zh' 或 'en'


class BaseCollector:
    """
    采集器基类。
    子类只需实现 fetch() -> list[RawItem] 方法。
    基类提供 HTTP 会话管理、UA轮换、重试和 safe_fetch 容错包装。
    """

    def __init__(self, name: str):
        self.name = name
        self._session: Optional[requests.Session] = None
        self._user_agents = USER_AGENTS.copy()
        self._ua_index = 0

    @property
    def session(self) -> requests.Session:
        """延迟创建带重试策略的 requests.Session"""
        if self._session is None:
            self._session = requests.Session()
            retry_strategy = Retry(
                total=RETRY_COUNT,
                backoff_factor=RETRY_BACKOFF_FACTOR,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "HEAD"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)
        return self._session

    def _random_ua(self) -> str:
        """随机选择 User-Agent"""
        return random.choice(self._user_agents)

    def _get_headers(self) -> dict:
        """构建请求头"""
        return {
            "User-Agent": self._random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def _get(self, url: str, timeout: int = REQUEST_TIMEOUT, **kwargs) -> requests.Response:
        """
        HTTP GET 请求，带重试和指数退避。
        如果所有重试都失败，抛出最后的异常。
        """
        last_exception = None
        for attempt in range(RETRY_COUNT):
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=timeout,
                    **kwargs,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exception = e
                wait = RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(
                    "[%s] GET %s 失败 (第%d次): %s，%d秒后重试",
                    self.name, url[:80], attempt + 1, e, wait,
                )
                time.sleep(wait)

        logger.error("[%s] GET %s 所有%d次重试均失败", self.name, url[:80], RETRY_COUNT)
        raise last_exception  # type: ignore[misc]

    def _safe_fetch(self) -> list[RawItem]:
        """
        容错包装器：调用 fetch()，捕获所有异常，返回空列表。
        保证采集器的异常不会中断整个流水线。
        """
        try:
            logger.info("[%s] 开始采集...", self.name)
            items = self.fetch()
            logger.info("[%s] 采集完成，获取 %d 条", self.name, len(items))
            return items
        except Exception as e:
            logger.error("[%s] 采集失败: %s", self.name, e, exc_info=True)
            return []

    def fetch(self) -> list[RawItem]:
        """
        子类必须实现此方法。
        返回标准化的 RawItem 列表。
        """
        raise NotImplementedError(f"{self.__class__.__name__}.fetch() 必须被实现")

    def close(self):
        """关闭 HTTP 会话"""
        if self._session is not None:
            self._session.close()
            self._session = None
