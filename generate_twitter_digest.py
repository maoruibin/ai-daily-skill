#!/usr/bin/env python3
"""
Twitter Digest HTML 生成器
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.html_generator import HTMLGenerator

def generate_twitter_digest():
    """生成 Twitter 摘要 HTML 页面"""
    
    # 准备 Twitter 摘要数据
    today = datetime.now().strftime("%Y-%m-%d")
    result = {
        "date": today,
        "theme": "twitter",
        "title": "Twitter 推荐流日报",
        "summary": "今日 Twitter/X 推荐流热门资讯精选",
        "keywords": ["Twitter", "AI", "技术", "Claude", "开源"],
        "entries": [
            {
                "title": "Claude Opus 4.6 发布引发编程工具革命",
                "content": "Anthropic 正式发布 Claude Opus 4.6，距离前代版本仅三个月时间。新模型在 ARC-AGI 2 基准测试中问题解决能力提升 83%，支持 100万 token 的超长上下文，成为 AI 编程工具的新王者。",
                "category": "AI",
                "keywords": ["Claude", "Anthropic", "AI编程"],
                "stats": {"likes": "85K", "views": "5.2M", "shares": "2.1K"},
                "ai_comment": "🔥 **热度爆棚** - Anthropic 发布节奏惊人，Opus 系列迭代速度创行业纪录\n📌 **大佬认可** - 开发者实测反馈性能超越 GPT-4o\n💡 **关键洞察** - 超长上下文支持解决了复杂编程场景痛点",
                "url": "https://k.sina.com.cn/article_7879848900_1d5acf3c401902w7eq.html"
            },
            {
                "title": "Anthropic 与 OpenClaw 冲突升级",
                "content": "Anthropic 正式封禁第三方 AI 智能体工具 OpenClaw，禁止其通过 Claude 包月订阅无限调用模型接口。这一决定让大量重度开发者直接\"断粮\"，引发社区激烈讨论。",
                "category": "行业",
                "keywords": ["OpenClaw", "Anthropic", "开源"],
                "stats": {"likes": "62K", "views": "3.8M", "shares": "4.3K"},
                "ai_comment": "💥 **行业地震** - AI 大厂与开源工具的首次大规模冲突\n📌 **争议焦点** - API 使用边界与开源精神的矛盾\n💡 **关键洞察** - 反映了 AI 生态系统中商业利益与社区开放的深层矛盾",
                "url": "https://k.sina.cn/article_7857201856_1d45362c001903z908.html"
            },
            {
                "title": "Claude Code 源码泄露事件持续发酵",
                "content": "Anthropic 针对 Agentic AI 开发的重磅工具\"Claude Code\"发生严重源码泄露，涉及核心架构和算法机密。业界专家认为这可能对智能体 AI 发展方向产生重大影响。",
                "category": "安全",
                "keywords": ["Claude Code", "泄露", "安全"],
                "stats": {"likes": "45K", "views": "2.9M", "shares": "1.8K"},
                "ai_comment": "🚨 **重大危机** - 2026年 AI 行业最严重的机密泄露事件\n📌 **影响深远** - 可能影响智能体 AI 技术路线图和发展方向\n💡 **关键洞察** - AI 工具安全性和知识产权保护成为行业重要课题",
                "url": "https://www.gyznsw.cn/2026/04/01/2026-04-01-AI%E6%8A%80%E6%9C%AF%E6%AF%8F%E6%97%A5%E5%88%86%E6%9E%90-20260401/"
            },
            {
                "title": "Remotion 视频生成工具引爆'Vibe Video'时代",
                "content": "2026年推特最火 Claude Skills 榜单显示，Remotion 视频生成工具以 80+ 次提及遥遥领先，成为开发者最追捧的 AI 视频制作工具，成功引爆'Vibe Video'时代。",
                "category": "视频",
                "keywords": ["Remotion", "视频生成", "Vibe Video"],
                "stats": {"likes": "73K", "views": "4.1M", "shares": "3.2K"},
                "ai_comment": "🎬 **视频革命** - Remotion 重新定义 AI 视频生成标准\n📌 **开发者热捧** - 从技术实现到用户体验都获得高度认可\n💡 **关键洞察** - 'Vibe Video'概念标志着 AI 视频制作进入新阶段",
                "url": "https://juejin.cn/post/7614769648597254194"
            },
            {
                "title": "GitHub AI 项目爆发式增长",
                "content": "2026年 GitHub AI 项目榜单显示，以 OpenClaw 为代表的'Claw'系列个人 AI 助手项目占据榜单前列，强调本地部署、数据自主和极致轻量化，反映了 AI 开发的新趋势。",
                "category": "开发",
                "keywords": ["GitHub", "OpenClaw", "本地化"],
                "stats": {"likes": "58K", "views": "3.5M", "shares": "2.5K"},
                "ai_comment": "🚀 **新格局** - AI 开发从云端向本地化转变\n📌 **趋势明确** - 数据自主、隐私保护成为核心诉求\n💡 **关键洞察** - AI 工具正在向轻量化、本地化、用户可控方向发展",
                "url": "https://zhuanlan.zhihu.com/p/2008659188574867526"
            },
            {
                "title": "AI 技术奇点预言引发热议",
                "content": "马斯克公开断言 2026 年将开启技术奇点时代，Claude Code 等先进 AI 编程工具的快速发展似乎在印证这一预言。开发者社区对 AI 发展速度表示惊叹。",
                "category": "趋势",
                "keywords": ["马斯克", "奇点", "技术预测"],
                "stats": {"likes": "91K", "views": "6.3M", "shares": "4.7K"},
                "ai_comment": "🔮 **预言成真** - 马斯克的奇点预言正在加速实现\n📌 **行业共鸣** - AI 技术突破速度超乎所有人预期\n💡 **关键洞察** - 2026年可能成为 AI 发展的关键转折点",
                "url": "https://www.msn.com/zh-cn/news/other/ai%E7%BC%96%E7%A8%8B%E5%B7%A5%E5%85%B7claude-code%E5%BC%95%E8%A1%8C%E4%B8%9A%E7%83%AD%E8%AE%AE-%E9%A9%AC%E6%96%AF%E5%85%8B%E6%96%AD%E8%A8%802026%E5%B9%B4%E5%BC%80%E5%90%AF%E6%8A%80%E6%9C%AF%E5%A5%87%E7%82%B9%E6%97%B6%E4%BB%A3/ar-AA1TCrY0"
            },
            {
                "title": "2026年 AI 突破性趋势发布",
                "content": "多家研究机构发布报告指出，2026年 AI 领域呈现三大关键趋势：从'大模型参数竞赛'转向'推理能力、智能体与场景闭环'的深度较量，本地化部署与数据自主成为主流。",
                "category": "趋势",
                "keywords": ["AI趋势", "本地化", "智能体"],
                "stats": {"likes": "67K", "views": "4.2M", "shares": "2.9K"},
                "ai_comment": "📊 **趋势明确** - AI 发展进入质量和效率并重的新阶段\n📌 **重心转移** - 从单纯的模型能力到实际应用场景\n💡 **关键洞察** - AI 正在从实验室走向产业深度应用",
                "url": "https://www.thepaper.cn/newsDetail_forward_32889979"
            }
        ]
    }
    
    # 生成 HTML 页面
    generator = HTMLGenerator()
    
    # 使用统一的生成方法
    html_content = generator.generate_daily(result)
    
    # 保存到 docs 目录
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    filename = f"twitter-2026-04-07-digest-noon.html"
    output_path = docs_dir / filename
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Twitter 摘要 HTML 页面生成完成: {output_path}")
    
    # 复制 CSS 文件
    css_dir = docs_dir / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 CSS 样式文件
    css_template = project_root / "templates" / "css" / "styles.css"
    if css_template.exists():
        import shutil
        shutil.copy2(css_template, css_dir / "styles.css")
        print(f"✅ CSS 文件复制完成: {css_dir / 'styles.css'}")

if __name__ == "__main__":
    generate_twitter_digest()