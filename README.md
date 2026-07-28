# 🤖 AI Daily Briefing — 全球AI大模型日报

每日自动采集全球AI大模型和应用的最新信息，通过 DeepSeek API 进行智能摘要和分类，生成移动端 H5 简报页面。

## 架构

```
采集层 (collector/)  →  处理层 (processor/)  →  存储层 (storage/)  →  展示层 (web/)
                                                                ↓
                                                          GitHub Pages
```

### 数据来源

| 采集器 | 来源 | 类型 |
|--------|------|------|
| RSS Fetcher | 机器之心、量子位、The Verge、TechCrunch、VentureBeat 等 | RSS/Atom Feed |
| ArXiv Fetcher | arxiv.org (cs.AI, cs.CL, cs.LG, cs.CV) | 学术论文 |
| GitHub Trending | github.com/trending | AI开源项目 |
| HuggingFace | huggingface.co/papers + trending models | 论文 & 模型 |
| Product Hunt | producthunt.com/topics/ai | AI产品发布 |

### 简报分类

- **模型发布** — 大语言模型、多模态模型、开源模型等
- **应用产品** — AI应用、工具、产品功能更新
- **研究前沿** — 论文、技术突破、新架构
- **投融资** — 融资、并购、IPO
- **政策监管** — 法规、伦理、安全治理

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key（从 https://platform.deepseek.com/api_keys 获取）
```

或设置环境变量：

```bash
# Windows
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Linux/macOS
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 验证 API 连通性

```bash
python scripts/verify_api.py
```

### 4. 运行每日采集

```bash
# 采集今天的新闻
python scripts/daily_run.py

# 采集指定日期
python scripts/daily_run.py 2026-07-27
```

### 5. 查看简报

在浏览器中打开 `web/index.html`，或部署到 GitHub Pages。

## 部署到 GitHub Pages

### 方式一：直接部署 web/ 目录

1. 将 `web/` 目录推送到 GitHub 仓库
2. 在仓库 Settings → Pages 中设置 Source 为 `main` 分支的 `/web` 目录
3. 访问 `https://<username>.github.io/<repo>/`

### 方式二：gh-pages 分支

```bash
git subtree push --prefix web origin gh-pages
```

## 定时自动运行

### Windows (Task Scheduler)

1. 打开"任务计划程序"
2. 创建基本任务 → 每天 8:00 AM
3. 操作：启动程序
   - 程序：`python`
   - 参数：`scripts/daily_run.py`
   - 起始于：`C:\Users\Administrator\Desktop\ai信息采集`

### Linux/macOS (cron)

```bash
# 每天早上 8:00 运行
0 8 * * * cd /path/to/ai信息采集 && python scripts/daily_run.py >> logs/daily.log 2>&1
```

## 项目结构

```
ai信息采集/
├── collector/           # 数据采集层
│   ├── base.py          # 基类：会话管理、UA轮换、重试
│   ├── rss_fetcher.py   # RSS采集
│   ├── arxiv_fetcher.py # ArXiv论文
│   ├── github_trending.py # GitHub热门项目
│   ├── huggingface.py   # HuggingFace论文+模型
│   └── producthunt.py   # Product Hunt产品
├── processor/           # 数据处理层
│   ├── schema.py        # 数据模型定义
│   ├── deduplicator.py  # 去重
│   ├── summarizer.py    # DeepSeek API摘要
│   └── aggregator.py    # 聚合生成简报
├── storage/
│   ├── raw/             # 原始采集数据
│   └── briefings/       # 最终简报JSON
├── web/
│   ├── index.html       # H5简报页面
│   └── briefings/       # 简报数据副本（供前端加载）
├── scripts/
│   ├── config.py        # 集中配置
│   ├── daily_run.py     # 主编排脚本
│   └── verify_api.py    # API验证
├── requirements.txt
└── README.md
```

## 成本估算

使用 DeepSeek V3 (deepseek-chat)，日均处理约 50-80 条新闻：

- 输入 Token：~15,000
- 输出 Token：~10,000
- DeepSeek 定价：¥1/M 输入, ¥2/M 输出
- **日均费用：约 ¥0.035（~$0.005）**
- **月均费用：约 ¥1（~$0.14）**

> DeepSeek 的成本远低于其他商用API，非常适合每日自动化任务。

## License

MIT
