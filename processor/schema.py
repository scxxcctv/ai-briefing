"""
数据模式定义 - 系统中所有结构化数据类型
使用 TypedDict 以便于 IDE 类型提示和 JSON 序列化
"""
from typing import TypedDict, Optional
from typing import List as ListType


class EntitySet(TypedDict, total=False):
    """提取的关键实体"""
    companies: ListType[str]
    models: ListType[str]
    people: ListType[str]
    technologies: ListType[str]


class SummarizedItem(TypedDict):
    """Claude 处理后的单条简报条目"""
    id: str
    title_zh: str
    title_en: str
    summary_zh: str               # 50-80字中文摘要
    source_name: str
    source_url: str
    published_at: str             # ISO格式
    category: str                 # 模型发布 | 应用产品 | 研究前沿 | 投融资 | 政策监管
    subcategory: str              # 更细粒度分类
    importance: int               # 1-5 星
    entities: EntitySet
    tags: ListType[str]           # 5-8个标签
    is_trending: bool
    related_item_ids: ListType[str]


class CategoryStat(TypedDict):
    """分类统计"""
    count: int
    items: ListType[str]          # 条目ID列表


class BriefingStats(TypedDict):
    """简报统计信息"""
    sources_count: int
    total_collected_raw: int
    total_after_dedup: int
    total_published: int
    api_tokens_input: int
    api_tokens_output: int
    api_cost_estimate_usd: float


class DailyBriefing(TypedDict):
    """每日简报的完整数据结构"""
    date: str                     # YYYY-MM-DD
    generated_at: Optional[str]   # ISO格式时间戳
    model: Optional[str]          # 使用的Claude模型
    briefing_summary: Optional[str]  # 200-300字总体摘要
    total_items: int
    categories: dict[str, CategoryStat]  # 按分类组织
    items: ListType[SummarizedItem]      # 所有条目
    stats: BriefingStats


def empty_briefing(date: str) -> DailyBriefing:
    """生成空的每日简报结构"""
    return DailyBriefing(
        date=date,
        generated_at=None,
        model=None,
        briefing_summary=None,
        total_items=0,
        categories={},
        items=[],
        stats=BriefingStats(
            sources_count=0,
            total_collected_raw=0,
            total_after_dedup=0,
            total_published=0,
            api_tokens_input=0,
            api_tokens_output=0,
            api_cost_estimate_usd=0.0,
        ),
    )
