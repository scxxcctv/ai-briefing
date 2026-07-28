"""
摘要器 - 使用 DeepSeek API 对新闻条目进行摘要、分类、实体提取和评分
DeepSeek API 兼容 OpenAI SDK
"""
import json
import logging
import re
import hashlib
import time

from openai import OpenAI

from collector.base import RawItem
from processor.schema import SummarizedItem, EntitySet
from scripts.config import BATCH_SIZE, CATEGORIES, DEEPSEEK_BASE_URL

logger = logging.getLogger(__name__)

# ============================================================
# 系统提示 — 保持不变
# ============================================================
SYSTEM_PROMPT = """你是一位专业的AI行业新闻编辑。你的任务是将一批AI相关新闻条目处理成结构化的中文简报。

## 处理要求

对于每个条目：
1. **中文标题**：将原标题翻译/总结为简洁的中文标题（15-30字）
2. **中文摘要**：撰写50-80字的中文摘要，突出核心信息
3. **保留英文标题**：保留原标题（英文则原样保留，中文则保留原文）
4. **分类**：归入以下类别之一：
   - 模型发布：大语言模型、多模态模型、开源模型等新模型发布与更新
   - 应用产品：AI应用、工具、产品发布与功能更新
   - 研究前沿：论文、技术突破、新架构、训练方法等前沿研究
   - 投融资：AI公司融资、并购、IPO等资本动态
   - 政策监管：AI相关法规、政策、伦理、安全治理
   - 商业商机：AI行业趋势分析、商业机会洞察、市场机会与商业化策略
5. **子分类**：在所属大类下的更细粒度标签（如"大语言模型"、"AI编程"、"图像生成"等）
6. **重要性评分**（1-5星）：
   - 5星：重大行业变革（如GPT-5发布、千亿级融资）
   - 4星：重要进展（主要模型更新、重要产品发布）
   - 3星：值得关注（有趣的研究、新创产品）
   - 2星：一般动态（小更新、常规报道）
   - 1星：信息性但非关键
7. **实体提取**：从内容中提取公司名、模型名、人物、技术
8. **标签**：5-8个关键词标签
9. **是否热门**：判断是否为当日热门话题（is_trending: true/false）

## 输出格式

严格按照以下JSON数组格式输出，不要包含任何其他文字：

```json
[
  {
    "id": "使用item_id字段的值",
    "title_zh": "中文标题",
    "title_en": "英文原标题或中文原文",
    "summary_zh": "50-80字中文摘要",
    "category": "模型发布",
    "subcategory": "大语言模型",
    "importance": 5,
    "entities": {
      "companies": ["company names"],
      "models": ["model names"],
      "people": ["people names"],
      "technologies": ["technology names"]
    },
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "is_trending": true
  }
]
```

注意：
- 输出必须是有效的JSON数组，不要有markdown包裹
- 每条输出必须与输入一一对应
- 对于无法分类的条目，使用最适合的类别
- 实体和标签为空时使用空数组[]
- 每个条目必须有id字段
"""


class Summarizer:
    """DeepSeek API 摘要处理器 (OpenAI 兼容)"""

    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _make_item_id(self, title: str, url: str) -> str:
        """为条目生成唯一ID"""
        return hashlib.md5(f"{title}{url}".encode()).hexdigest()[:12]

    def _build_batch_prompt(self, items: list[RawItem]) -> str:
        """将一批 RawItem 构建为提示文本"""
        lines = ["请处理以下AI新闻条目：\n"]
        for i, item in enumerate(items):
            item_id = self._make_item_id(item.get('title', ''), item.get('url', ''))
            lines.append(f"--- 条目 {i+1} ---")
            lines.append(f"item_id: {item_id}")
            lines.append(f"title: {item.get('title', '')}")
            lines.append(f"source: {item.get('source_name', '')}")
            lines.append(f"url: {item.get('url', '')}")
            lines.append(f"published: {item.get('published_at', '')}")
            lines.append(f"language: {item.get('language', 'en')}")
            lines.append(f"content: {item.get('raw_text', '')[:500]}")
            lines.append("")
        return "\n".join(lines)

    def _parse_response(self, response_text: str, items: list[RawItem]) -> list[SummarizedItem]:
        """解析 API 的 JSON 响应"""
        text = response_text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

        try:
            data = json.loads(text)
            if not isinstance(data, list):
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            data = v
                            break
                if not isinstance(data, list):
                    logger.error("响应不是JSON数组: %s", text[:200])
                    return []
        except json.JSONDecodeError:
            match = re.search(r'\[[\s\S]*\]', text)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.error("无法解析JSON: %s", text[:200])
                    return []
            else:
                logger.error("无法解析JSON: %s", text[:200])
                return []

        if not isinstance(data, list):
            return []

        results: list[SummarizedItem] = []
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                continue

            if i < len(items):
                raw = items[i]
                default_id = self._make_item_id(raw.get('title', ''), raw.get('url', ''))
                default_url = raw.get('url', '')
                default_source = raw.get('source_name', '')
                default_published = raw.get('published_at', '')
            else:
                default_id = entry.get('id', hashlib.md5(str(i).encode()).hexdigest()[:12])
                default_url = ''
                default_source = ''
                default_published = ''

            results.append(SummarizedItem(
                id=entry.get('id', default_id),
                title_zh=entry.get('title_zh', raw.get('title', '') if i < len(items) else ''),
                title_en=entry.get('title_en', raw.get('title', '') if i < len(items) else ''),
                summary_zh=entry.get('summary_zh', ''),
                source_name=default_source,
                source_url=entry.get('source_url', default_url),
                published_at=entry.get('published_at', default_published),
                category=entry.get('category', '应用产品'),
                subcategory=entry.get('subcategory', ''),
                importance=min(5, max(1, int(entry.get('importance', 3)))),
                entities=EntitySet(
                    companies=entry.get('entities', {}).get('companies', []),
                    models=entry.get('entities', {}).get('models', []),
                    people=entry.get('entities', {}).get('people', []),
                    technologies=entry.get('entities', {}).get('technologies', []),
                ),
                tags=entry.get('tags', []),
                is_trending=bool(entry.get('is_trending', False)),
                related_item_ids=entry.get('related_item_ids', []),
            ))

        return results

    def process_batch(self, items: list[RawItem], retry: bool = True) -> list[SummarizedItem]:
        """
        处理一批 RawItem，返回 SummarizedItem 列表。
        如果 JSON 解析失败且 retry=True，会重试一次。
        """
        if not items:
            return []

        prompt = self._build_batch_prompt(items)

        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.3,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )

                # 追踪token使用
                usage = response.usage
                self.total_input_tokens += usage.prompt_tokens
                self.total_output_tokens += usage.completion_tokens

                # 提取响应文本
                response_text = response.choices[0].message.content or ""

                result = self._parse_response(response_text, items)
                if result:
                    logger.info("批次处理成功: %d 条 (attempt %d)", len(result), attempt + 1)
                    return result

                if retry and attempt == 0:
                    logger.warning("JSON解析返回空，准备重试...")
                    prompt = "上次响应格式不正确，请严格输出JSON数组。\n\n" + prompt
                    time.sleep(2)
                    continue

            except Exception as e:
                logger.error("DeepSeek API 错误: %s", e)
                if attempt == 0 and retry:
                    time.sleep(3)
                    continue
                return []

        return []

    def estimate_cost(self) -> float:
        """
        估算API费用（基于 DeepSeek 定价）
        deepseek-chat: ¥1/M 输入, ¥2/M 输出（约 $0.14/M 输入, $0.28/M 输出）
        """
        input_cost = (self.total_input_tokens / 1_000_000) * 0.14
        output_cost = (self.total_output_tokens / 1_000_000) * 0.28
        return round(input_cost + output_cost, 4)
