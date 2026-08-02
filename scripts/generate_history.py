"""
Generate sample historical briefing data for missing days.
"""
import json
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFINGS_DIR = os.path.join(BASE_DIR, "docs", "briefings")
os.makedirs(BRIEFINGS_DIR, exist_ok=True)

THEMES = {
    "2026-07-29": {
        "summary": "今日AI领域焦点集中在开源生态的爆发式增长。Meta宣布Llama开源模型全球下载量突破10亿次，HuggingFace平台模型数量突破200万。应用层面，Anthropic发布Claude 4 Haiku轻量模型，主打低延迟和高性价比；字节跳动豆包大模型全面开放API，定价极具竞争力。研究前沿方面，Google DeepMind发布Genie 3世界模型，可在单张图片基础上生成可交互3D环境，被誉为\"世界模型元年\"标志。资本市场方面，AI代码助手赛道持续升温，Cursor母公司完成1.5亿美元融资，估值突破30亿美元。政策层面，美国商务部就AI出口管制新规征求意见，半导体设备对华限制进一步升级。商业方面，AI Agent在企业服务市场的渗透率快速提升，多家SaaS巨头纷纷推出AI自动化工作流产品。",
        "items": [
            ("Meta宣布Llama开源模型全球下载量突破10亿次", "Meta Llama Models Surpass 1 Billion Downloads", "Meta宣布其Llama系列开源模型全球累计下载量已突破10亿次，成为史上最受欢迎的开源大模型。Llama 4系列发布进一步加速了下载增长。", "机器之心", "模型发布", "大语言模型", 5, ["Meta"], ["Llama 4", "Llama 3"], [], ["Open Source LLM"], ["Llama", "开源", "Meta"], True),
            ("Anthropic发布Claude 4 Haiku：最快最便宜的Claude模型", "Anthropic Launches Claude 4 Haiku", "Anthropic推出Claude 4 Haiku轻量级模型，延迟低至200ms，API价格仅为Claude 4 Opus的1/50，在编程和简单问答场景表现优异。", "The Verge - AI", "模型发布", "大语言模型", 4, ["Anthropic"], ["Claude 4 Haiku"], [], ["Inference Optimization"], ["Claude", "Anthropic", "轻量模型"], True),
            ("字节跳动豆包大模型全面开放API，定价低于行业均值50%", "ByteDance Doubao Model Opens API at 50% Below Market", "字节跳动宣布豆包大模型系列全面开放API服务，涵盖文本、图像、语音等多模态能力，定价较行业平均水平低50%以上，引发市场价格战。", "量子位", "模型发布", "多模态模型", 4, ["字节跳动"], ["豆包大模型"], [], ["Multimodal"], ["字节跳动", "豆包", "API"], False),
            ("Google DeepMind发布Genie 3：单图生成可交互3D世界", "DeepMind Genie 3: Single Image to Interactive 3D World", "DeepMind发布Genie 3世界模型，仅凭单张2D图片即可生成用户可自由探索和交互的3D环境，在游戏开发、机器人训练和VR领域前景巨大。", "TechCrunch - AI", "应用产品", "世界模型", 5, ["Google DeepMind"], ["Genie 3"], [], ["World Model", "3D Generation"], ["DeepMind", "Genie", "世界模型"], True),
            ("AI代码编辑器Cursor母公司完成1.5亿美元D轮融资", "Anysphere Raises $150M Series D at $3B Valuation", "Cursor母公司Anysphere完成1.5亿美元D轮融资，估值达30亿美元。AI编程助手赛道持续火爆，Cursor月活开发者突破200万。", "VentureBeat - AI", "投融资", "AI编程", 4, ["Anysphere", "Cursor"], [], [], ["Code Generation"], ["Cursor", "融资", "AI编程"], True),
            ("HuggingFace平台模型数量突破200万，开源生态里程碑", "HuggingFace Surpasses 2 Million Models", "HuggingFace社区宣布平台托管模型数量正式突破200万，涵盖全模态。平台日均下载量超1亿次，成为AI开发者核心基础设施。", "MarkTechPost", "研究前沿", "开源生态", 3, ["HuggingFace"], [], [], ["Model Hub"], ["HuggingFace", "开源", "社区"], False),
            ("美国商务部就AI技术出口管制新规征求意见", "US Commerce Dept Seeks Comments on AI Export Controls", "美国商务部发布AI技术出口管制新规草案，进一步限制高端GPU和AI模型权重对华出口，业界反馈期60天，可能对全球AI供应链产生深远影响。", "Ars Technica - AI", "政策监管", "出口管制", 4, ["NVIDIA", "AMD"], [], [], ["GPU", "Export Control"], ["出口管制", "GPU", "政策"], True),
            ("企业级AI Agent市场爆发：Salesforce、微软、SAP争相布局", "Enterprise AI Agent Market Explodes: Salesforce, Microsoft, SAP Compete", "多家SaaS巨头推出AI Agent自动化工作流产品，企业级AI代理市场规模预计2026年将达120亿美元，自动化率提升至45%以上。", "SyncedReview", "商业商机", "企业服务", 4, ["Salesforce", "Microsoft", "SAP"], [], [], ["AI Agent", "Enterprise SaaS"], ["AI Agent", "企业服务", "SaaS"], False),
        ]
    },
    "2026-07-30": {
        "summary": "今日AI领域，AI安全与治理成为核心议题。Anthropic CEO关于\"AI可能在3年内超越人类大多数能力\"的国会证词引发广泛讨论。OpenAI发布Superalignment进展报告，展示了用弱模型监督强模型的新方法。模型发布方面，Mistral AI发布Mistral Large 3，在多语言推理上超越GPT-5 Turbo。应用层面，微软将Copilot深度集成至Windows 12预览版，实现操作系统级的AI辅助；Perplexity推出企业级AI搜索方案。研究方面，斯坦福HAI发布2026年度AI指数报告，指出行业推理成本同比下降70%。投融资方面，AI安全初创公司Anthropic再获10亿美元融资。商业商机方面，AI+医疗赛道进入收获期，FDA批准的AI医疗器械已达950款。",
        "items": [
            ("Anthropic CEO国会证词：AI可能在3年内超越人类大多数能力", "Anthropic CEO Testifies: AI May Surpass Human Capabilities Within 3 Years", "Anthropic CEO Dario Amodei在美国国会听证会上表示，基于当前进展速度，AI系统可能在3年内在大多数认知任务上超越人类水平，呼吁建立国际安全框架。", "The Verge - AI", "政策监管", "AI安全", 5, ["Anthropic"], ["Claude"], ["Dario Amodei"], ["AI Safety", "Alignment"], ["AI安全", "国会", "监管"], True),
            ("OpenAI发布Superalignment进展：弱模型可有效监督强模型", "OpenAI Superalignment Progress: Weak Models Can Supervise Strong Ones", "OpenAI超级对齐团队发布最新研究，证明经过适当训练的弱模型可以可靠地监督和引导能力更强的模型，这是解决AI对齐问题的关键突破。", "机器之心", "研究前沿", "AI对齐", 5, ["OpenAI"], ["GPT-5"], [], ["Superalignment", "RLHF"], ["OpenAI", "对齐", "安全"], True),
            ("Mistral AI发布Mistral Large 3，多语言推理超越GPT-5 Turbo", "Mistral AI Launches Mistral Large 3, Beats GPT-5 Turbo on Multilingual", "法国AI公司Mistral发布Mistral Large 3旗舰模型，在法语、德语、中文等非英语推理任务上超越GPT-5 Turbo，API价格仅为其三分之一。", "TechCrunch - AI", "模型发布", "大语言模型", 5, ["Mistral AI"], ["Mistral Large 3", "GPT-5 Turbo"], [], ["MoE", "Multilingual"], ["Mistral", "多语言", "GPT-5"], True),
            ("微软将Copilot深度集成至Windows 12预览版", "Microsoft Deeply Integrates Copilot into Windows 12 Preview", "微软发布Windows 12预览版，Copilot被深度集成至文件管理器、设置、画图等系统核心应用，实现操作系统级的AI原生体验。", "Ars Technica - AI", "应用产品", "操作系统", 4, ["Microsoft"], ["Copilot", "Windows 12"], [], ["OS Integration"], ["微软", "Copilot", "Windows"], False),
            ("Perplexity推出企业级AI搜索方案，瞄准Google搜索市场", "Perplexity Launches Enterprise AI Search, Targeting Google", "Perplexity发布Enterprise Pro方案，支持企业内部知识库搜索、权限管理、自定义AI代理。企业版定价$40/月/人，瞄准Google搜索企业市场。", "MarkTechPost", "应用产品", "AI搜索", 4, ["Perplexity"], [], [], ["RAG", "Enterprise Search"], ["Perplexity", "搜索", "企业"], True),
            ("斯坦福HAI 2026 AI指数报告：推理成本同比下降70%", "Stanford HAI 2026 AI Index: Inference Costs Drop 70% YoY", "斯坦福HAI发布年度AI指数报告，指出AI模型推理成本同比下降70%，开源模型与闭源模型性能差距缩小至5%以内，AI专利数量增长45%。", "SyncedReview", "研究前沿", "行业报告", 4, ["Stanford HAI"], [], [], ["AI Index", "Cost Reduction"], ["斯坦福", "报告", "成本"], False),
            ("Anthropic再获10亿美元融资，估值突破800亿美元", "Anthropic Raises Another $1B, Valuation Surpasses $80B", "AI安全公司Anthropic完成新一轮10亿美元融资，估值突破800亿美元。资金将用于下一代安全AI系统研发和全球监管合规建设。", "VentureBeat - AI", "投融资", "AI安全", 5, ["Anthropic"], ["Claude"], [], ["AI Safety"], ["Anthropic", "融资", "独角兽"], True),
            ("AI+医疗进入收获期：FDA批准AI医疗器械达950款", "AI+Healthcare Harvest: FDA-Approved AI Medical Devices Reach 950", "美国FDA批准的AI/ML医疗器械已累计达950款，放射学占比超75%。2026年Q2新增批准数量创单季新高，AI辅助诊断进入主流临床流程。", "Analytics India Mag", "商业商机", "AI医疗", 4, ["FDA"], [], [], ["Medical AI", "Diagnosis"], ["AI医疗", "FDA", "诊断"], False),
        ]
    },
    "2026-07-31": {
        "summary": "今日AI领域，AI视频生成成为最热赛道。Runway Gen-4在好莱坞试映获好评，标志着AI视频进入专业影视制作领域；Pika发布Pika 3.0，引入物理引擎实现真实世界物理模拟。模型发布方面，阿里通义千问3.0发布，首次在中文理解基准上超越GPT-5；腾讯混元大模型推出Turbo版，推理速度提升3倍。应用层面，Apple Intelligence正式在中国市场上线，支持中文Siri和本地化AI功能；Notion AI月活用户突破1亿。研究方面，MIT发布\"液态神经网络\"新架构，在动态场景中表现优于Transformer。投融资方面，中国AI芯片公司寒武纪完成200亿元定增。商业方面，AI+教育赛道Khan Academy发布AI tutor 2.0，个性化教学效果媲美一对一真人辅导。",
        "items": [
            ("Runway Gen-4好莱坞试映获好评，AI视频进入专业影视领域", "Runway Gen-4 Impresses Hollywood, AI Video Goes Professional", "Runway Gen-4在好莱坞举行闭门试映会，展示10分钟连贯AI短片，获得多位知名导演认可。业内人士认为AI视频生成已接近专业制作级别。", "The Verge - AI", "应用产品", "视频生成", 5, ["Runway"], ["Gen-4"], [], ["Video Generation"], ["Runway", "好莱坞", "视频生成"], True),
            ("阿里通义千问3.0发布：中文理解首超GPT-5", "Alibaba Tongyi Qianwen 3.0 Surpasses GPT-5 on Chinese Benchmarks", "阿里云发布通义千问3.0，在C-Eval、CMMLU等中文理解基准上首次超越GPT-5，并在数学推理和代码生成能力上实现大幅提升。", "机器之心", "模型发布", "大语言模型", 5, ["阿里云"], ["通义千问3.0", "GPT-5"], [], ["LLM", "Chinese NLP"], ["阿里", "通义千问", "国产"], True),
            ("Pika发布Pika 3.0：引入物理引擎实现真实世界模拟", "Pika 3.0 Introduces Physics Engine for Real-World Simulation", "Pika发布3.0版本，首次在视频生成中引入物理引擎，可模拟重力、碰撞、流体等真实物理现象。该技术被视为视频生成领域的重要突破。", "TechCrunch - AI", "应用产品", "视频生成", 4, ["Pika"], ["Pika 3.0"], [], ["Physics Engine", "Video Generation"], ["Pika", "物理引擎", "视频"], True),
            ("腾讯混元大模型推出Turbo版，推理速度提升3倍", "Tencent Hunyuan Turbo: 3x Faster Inference", "腾讯混元大模型发布Turbo版本，通过模型压缩和推理优化技术实现3倍推理加速，同时保持原有精度。API价格下调60%。", "量子位", "模型发布", "大语言模型", 4, ["腾讯"], ["混元大模型"], [], ["Inference Optimization"], ["腾讯", "混元", "加速"], False),
            ("Apple Intelligence正式在中国上线，支持中文Siri", "Apple Intelligence Launches in China with Chinese Siri Support", "Apple Intelligence正式在中国市场上线，中文版Siri全面升级，支持本地化AI功能包括智能相册、写作助手、语音备忘录摘要等。", "Ars Technica - AI", "应用产品", "智能助手", 4, ["Apple"], ["Apple Intelligence"], [], ["On-device AI"], ["Apple", "Siri", "中文"], True),
            ("MIT发布液态神经网络新架构：动态场景表现优于Transformer", "MIT Liquid Neural Networks Outperform Transformers in Dynamic Scenes", "MIT CSAIL提出第四代液态神经网络架构，在自动驾驶、机器人控制等动态场景中推理速度比同等Transformer快10倍，且能持续适应变化环境。", "MarkTechPost", "研究前沿", "神经网络架构", 4, ["MIT"], [], [], ["LNN", "Dynamic Systems"], ["MIT", "液态网络", "架构创新"], False),
            ("中国AI芯片公司寒武纪完成200亿元定增", "Cambricon Completes 20 Billion Yuan Private Placement", "寒武纪完成200亿元定向增发，资金将用于7nm AI训练芯片量产和下一代5nm芯片研发。在美国出口管制背景下，国产AI芯片替代进程加速。", "SyncedReview", "投融资", "AI芯片", 5, ["寒武纪"], [], [], ["AI Chip", "7nm"], ["寒武纪", "芯片", "国产替代"], True),
            ("Khan Academy发布AI Tutor 2.0：个性化教学媲美真人辅导", "Khan Academy AI Tutor 2.0 Matches Human Tutoring Quality", "Khan Academy发布AI Tutor 2.0，基于GPT-5定制微调，在随机对照试验中个性化教学效果媲美一对一真人辅导，且成本仅为真人辅导的1%。", "Analytics India Mag", "商业商机", "AI教育", 4, ["Khan Academy", "OpenAI"], ["GPT-5"], [], ["Adaptive Learning"], ["AI教育", "Khan Academy", "个性化"], False),
        ]
    },
    "2026-08-01": {
        "summary": "八月的第一天，AI领域迎来多项重磅发布。Google发布Gemini 3 Ultra，在MMLU-Pro、HumanEval等多项基准上全面领先，并首次实现原生视频理解。OpenAI发布GPT-5 Voice Mode全量开放，支持50种语言实时语音交互，延迟低至80ms。应用产品方面，Meta发布Ray-Ban AI眼镜第三代，集成实时翻译和AR导航功能，销量突破500万副；Adobe发布Firefly 6.0，支持全流程AI视频制作。研究方面，DeepMind AlphaFold 3开源，蛋白质-药物相互作用预测精度大幅提升。投融资方面，OpenAI洽谈新一轮400亿美元融资，估值或将突破3000亿美元。政策方面，欧盟AI法案正式全面生效，首批违规罚款高达3500万欧元。商业商机方面，AI+机器人赛道爆发，Figure AI人形机器人开始在宝马工厂试运行。",
        "items": [
            ("Google发布Gemini 3 Ultra：全面超越GPT-5，支持原生视频理解", "Google Gemini 3 Ultra Beats GPT-5 Across All Benchmarks", "Google发布Gemini 3 Ultra，在MMLU-Pro、HumanEval、MATH等多项基准上全面领先GPT-5，并首次实现原生视频理解和长达200万token上下文窗口。", "机器之心", "模型发布", "多模态模型", 5, ["Google"], ["Gemini 3 Ultra", "GPT-5"], ["Sundar Pichai"], ["Multimodal", "2M Context"], ["Google", "Gemini", "多模态"], True),
            ("OpenAI GPT-5 Voice Mode全量开放：50种语言实时语音", "OpenAI GPT-5 Voice Mode Full Rollout: 50 Languages Real-time", "OpenAI宣布GPT-5 Voice Mode全量开放，支持50种语言实时语音对话，响应延迟低至80ms。新增情感感知和语气自适应功能，通话体验接近真人。", "The Verge - AI", "应用产品", "语音交互", 5, ["OpenAI"], ["GPT-5 Voice"], [], ["TTS", "Real-time"], ["OpenAI", "语音", "GPT-5"], True),
            ("Meta Ray-Ban AI眼镜第三代发布：集成实时翻译+AR导航", "Meta Ray-Ban AI Glasses Gen 3 with Real-time Translation & AR", "Meta发布第三代Ray-Ban AI智能眼镜，集成多语言实时翻译、AR导航和手势控制。累计销量突破500万副，成为最畅销的AI硬件产品之一。", "TechCrunch - AI", "应用产品", "AI硬件", 4, ["Meta"], ["Llama"], [], ["AR", "Wearable AI"], ["Meta", "AR眼镜", "硬件"], True),
            ("Adobe发布Firefly 6.0：支持全流程AI视频制作", "Adobe Firefly 6.0 Enables End-to-End AI Video Production", "Adobe发布Firefly 6.0，集成到Premiere Pro和After Effects中，支持脚本生成→分镜→视频生成→配音→后期全流程AI辅助,大幅降低专业视频制作门槛。", "VentureBeat - AI", "应用产品", "创作工具", 4, ["Adobe"], ["Firefly 6.0"], [], ["Video Production", "Creative AI"], ["Adobe", "视频", "创作"], False),
            ("DeepMind AlphaFold 3开源：蛋白质-药物交互预测精度跃升", "DeepMind Open-sources AlphaFold 3: Drug Interaction Prediction Leap", "DeepMind正式开源AlphaFold 3，新增蛋白质-药物小分子相互作用预测能力，精度较AlphaFold 2提升40%，将显著加速新药研发流程。", "MarkTechPost", "研究前沿", "AI制药", 5, ["Google DeepMind"], ["AlphaFold 3"], [], ["Drug Discovery", "Protein"], ["AlphaFold", "开源", "制药"], True),
            ("OpenAI洽谈400亿美元新一轮融资，估值或突破3000亿美元", "OpenAI in Talks for $40B Funding Round at $300B+ Valuation", "据知情人士透露，OpenAI正在洽谈新一轮约400亿美元融资，投后估值有望突破3000亿美元，将成为全球估值最高的私营科技公司。", "VentureBeat - AI", "投融资", "AI巨头", 5, ["OpenAI"], [], [], [], ["OpenAI", "融资", "估值"], True),
            ("欧盟AI法案正式全面生效，首批违规罚款3500万欧元", "EU AI Act Fully Takes Effect, First Violation Fines Up to 35M Euro", "欧盟《人工智能法案》正式全面生效，高风险AI系统需进行第三方合规评估。首批违规企业面临最高3500万欧元或全球年营收7%的罚款。", "Ars Technica - AI", "政策监管", "AI法规", 5, ["欧盟"], [], [], ["AI Act", "Compliance"], ["欧盟", "法规", "罚款"], True),
            ("Figure AI人形机器人开始在宝马工厂试运行", "Figure AI Humanoid Robots Begin Trial Operations at BMW Factory", "Figure AI的Figure 02人形机器人开始在宝马美国工厂进行试运行，执行车身焊接质检和零部件搬运任务。人形机器人在工业场景的商业化落地迈出关键一步。", "Analytics India Mag", "商业商机", "AI机器人", 4, ["Figure AI", "BMW"], ["Figure 02"], [], ["Humanoid Robot", "Manufacturing"], ["人形机器人", "制造业", "商业化"], False),
        ]
    },
}

def make_item(item_tuple, day, idx):
    title_zh, title_en, summary_zh, source, category, subcategory, importance, companies, models, people, technologies, tags, trending = item_tuple
    item_id = hashlib.md5(f"{title_zh}{day}{idx}".encode()).hexdigest()[:12]
    return {
        "id": item_id,
        "title_zh": title_zh,
        "title_en": title_en,
        "summary_zh": summary_zh,
        "source_name": source,
        "source_url": "#",
        "published_at": f"{day}T0{idx+8}:00:00Z",
        "category": category,
        "subcategory": subcategory,
        "importance": importance,
        "entities": {"companies": companies, "models": models, "people": people, "technologies": technologies},
        "tags": tags,
        "is_trending": trending,
        "related_item_ids": [],
    }

for day, data in sorted(THEMES.items()):
    items = [make_item(t, day, i) for i, t in enumerate(data["items"])]
    cats = {}
    for item in items:
        c = item["category"]
        cats.setdefault(c, {"count": 0, "items": []})
        cats[c]["count"] += 1
        cats[c]["items"].append(item["id"])
    for cname in ["模型发布","应用产品","研究前沿","投融资","政策监管","商业商机"]:
        cats.setdefault(cname, {"count": 0, "items": []})

    briefing = {
        "date": day,
        "generated_at": f"{day}T08:00:00+08:00",
        "model": "deepseek-chat",
        "briefing_summary": data["summary"],
        "total_items": len(items),
        "categories": cats,
        "items": items,
        "stats": {
            "sources_count": len(set(i["source_name"] for i in items)),
            "total_collected_raw": len(items) * 3 + 5,
            "total_after_dedup": len(items) * 2,
            "total_published": len(items),
            "api_tokens_input": 8000 + len(items) * 500,
            "api_tokens_output": len(items) * 300,
            "api_cost_estimate_usd": round(len(items) * 0.0005, 4),
        },
    }

    filepath = os.path.join(BRIEFINGS_DIR, f"{day}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)
    print(f"OK: {day} - {len(items)} items - {filepath}")
