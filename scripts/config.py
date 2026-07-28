"""
集中配置文件 - 所有可调参数和常量
"""
import os
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
RAW_DIR = STORAGE_DIR / "raw"
BRIEFINGS_DIR = STORAGE_DIR / "briefings"
WEB_DIR = BASE_DIR / "docs"
WEB_BRIEFINGS_DIR = WEB_DIR / "briefings"

# 确保目录存在
for d in [RAW_DIR, BRIEFINGS_DIR, WEB_BRIEFINGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# API 配置 (DeepSeek)
# ============================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ============================================================
# RSS 源配置
# ============================================================
RSS_FEEDS = {
    # 中文AI媒体
    "机器之心": "https://www.jiqizhixin.com/rss",
    "量子位": "https://www.qbitai.com/feed",
    # 英文科技媒体
    "The Verge - AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "TechCrunch - AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat - AI": "https://venturebeat.com/category/ai/feed/",
    "Ars Technica - AI": "https://feeds.arstechnica.com/arstechnica/technology",
    # AI专业媒体
    "Analytics India Mag": "https://analyticsindiamag.com/feed/",
    "MarkTechPost": "https://www.marktechpost.com/feed/",
    "SyncedReview": "https://syncedreview.com/feed/",
}

# ============================================================
# ArXiv 配置
# ============================================================
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.MA"]
ARXIV_MAX_RESULTS = 30
ARXIV_LOOKBACK_HOURS = 48

# ============================================================
# GitHub Trending 配置
# ============================================================
GITHUB_TRENDING_URL = "https://github.com/trending?since=daily"
GITHUB_AI_LANGUAGES = ["python", "javascript", "typescript", "jupyter notebook", "rust"]
GITHUB_AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "large language model",
    "machine learning", "deep learning", "neural", "diffusion",
    "transformer", "rag", "agent", "chatgpt", "gpt", "claude",
    "gemini", "llama", "mistral", "stable diffusion",
]

# ============================================================
# HuggingFace 配置
# ============================================================
HF_PAPERS_URL = "https://huggingface.co/papers"
HF_MODELS_URL = "https://huggingface.co/models?sort=trending&direction=-1"
HF_MAX_MODELS = 15

# ============================================================
# Product Hunt 配置
# ============================================================
PH_AI_TOPIC_URL = "https://www.producthunt.com/topics/ai"

# ============================================================
# 处理配置
# ============================================================
MAX_ITEMS_PER_SOURCE = 20
BATCH_SIZE = 15
DEDUP_TITLE_SIMILARITY_THRESHOLD = 0.85

# ============================================================
# 请求配置
# ============================================================
REQUEST_TIMEOUT = 30  # 秒
RETRY_COUNT = 3
RETRY_BACKOFF_FACTOR = 2  # 指数退避倍数

# ============================================================
# 用户代理列表
# ============================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

# ============================================================
# 简报分类定义
# ============================================================
CATEGORIES = {
    "模型发布": "大语言模型、多模态模型、开源模型等新模型发布与更新",
    "应用产品": "AI应用、工具、产品发布与功能更新",
    "研究前沿": "论文、技术突破、新架构、训练方法等前沿研究",
    "投融资": "AI公司融资、并购、IPO等资本动态",
    "政策监管": "AI相关法规、政策、伦理、安全治理",
}

# ============================================================
# 数据保留
# ============================================================
RAW_DATA_RETENTION_DAYS = 30
