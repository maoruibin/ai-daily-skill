#!/usr/bin/env python3
"""
AI Daily Report - 统一日报生成器

整合多个信息源：
1. Twitter 推荐流（通过浏览器自动化）
2. smol.ai RSS（AI 资讯聚合）

流程：
1. 刷 Twitter → 提取推文
2. 抓 RSS → 提取资讯
3. 小诸葛分析 → 提炼洞见 + 生成标题
4. 生成 HTML → 推送到 GitHub
5. 发送通知 → TG + 飞书
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    ZHIPU_API_KEY,
    OUTPUT_DIR,
    FEISHU_WEBHOOK_URL,
    RSS_SOURCES,
    KEYWORDS
)
from src.rss_fetcher import RSSFetcher
from src.claude_analyzer import ClaudeAnalyzer
from src.html_generator import HTMLGenerator


# ============================================================================
# 配置
# ============================================================================

# Telegram
TG_BOT_TOKEN = "8586904098:AAHUTjaiNtUvkqIO7UVSVFuOEFsNl-QVBaM"
TG_CHAT_ID = "8233389572"

# 飞书
FEISHU_WEBHOOK = FEISHU_WEBHOOK_URL or "https://open.feishu.cn/open-apis/bot/v2/hook/6233e120-38b6-4e1b-8f82-954ccc564052"

# 小诸葛 sessionKey
RESEARCHER_SESSION_KEY = "agent:researcher:main"

# 输出目录
DOCS_DIR = PROJECT_ROOT / "docs"


# ============================================================================
# 工具函数
# ============================================================================

def log(msg: str, level: str = "INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {msg}")


def generate_slug(title: str) -> str:
    """
    从标题生成 URL 友好的 slug
    
    示例：
    "Claude 发布 Cowork Agent 平台" → "claude-cowork-agent-platform"
    """
    # TODO: 调用 AI 翻译成英文，然后转 slug
    # 这里先用简单的拼音/时间戳方案
    import re
    from datetime import datetime
    
    # 移除特殊字符，转小写
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s]+', '-', slug)
    
    # 加上时间戳确保唯一
    timestamp = datetime.now().strftime("%H%M")
    
    return f"{slug[:50]}-{timestamp}"


def call_researcher_for_analysis(content: str) -> dict:
    """
    调用小诸葛进行深度分析
    
    返回：
    {
        "title": "主标题",
        "slug": "url-friendly-slug",
        "insights": ["洞察1", "洞察2"],
        "topics": ["话题1", "话题2"]
    }
    """
    # TODO: 使用 sessions_send 调用小诸葛
    # 目前先用简单的本地分析
    log("🧠 小诸葛分析中...")
    
    # 临时方案：返回基本信息
    return {
        "title": f"AI 日报 - {datetime.now().strftime('%Y-%m-%d')}",
        "slug": f"ai-daily-{datetime.now().strftime('%Y-%m-%d-%H%M')}",
        "insights": [
            "今日 AI 行业重点关注 Agent 平台发展",
            "模型能力持续提升，成本持续下降"
        ],
        "topics": ["AI", "Agent", "LLM"]
    }


# ============================================================================
# 信息源 1: Twitter
# ============================================================================

def fetch_twitter() -> list:
    """
    刷 Twitter 推荐流
    
    返回推文列表
    """
    log("🐦 开始刷 Twitter...")
    
    # TODO: 调用浏览器自动化
    # 目前返回空列表，等浏览器工具可用后实现
    log("⚠️  Twitter 抓取暂未实现，跳过", "WARN")
    return []


# ============================================================================
# 信息源 2: RSS
# ============================================================================

def fetch_rss() -> list:
    """
    抓取 RSS 源
    
    返回资讯列表
    """
    log("📡 开始抓 RSS...")
    
    fetcher = RSSFetcher()
    feeds = fetcher.fetch_multiple()
    all_entries = fetcher.get_all_entries_from_sources()
    filtered_entries = fetcher.filter_by_keywords(all_entries)
    
    log(f"✅ 抓取到 {len(filtered_entries)} 条资讯", "SUCCESS")
    return filtered_entries


# ============================================================================
# HTML 生成
# ============================================================================

def generate_html(analysis_result: dict, slug: str) -> str:
    """
    生成 HTML 页面
    
    返回文件路径
    """
    log("🎨 生成 HTML...")
    
    generator = HTMLGenerator()
    generator.generate_css()
    
    # 生成页面（使用 slug 作为文件名）
    html_path = generator.generate_daily_with_slug(analysis_result, slug)
    
    log(f"✅ HTML 已生成: {html_path}", "SUCCESS")
    return html_path


# ============================================================================
# Git 推送
# ============================================================================

def git_push(file_path: str, message: str):
    """推送到 GitHub"""
    log("📤 推送到 GitHub...")
    
    try:
        os.chdir(PROJECT_ROOT)
        
        # git add
        subprocess.run(["git", "add", file_path], check=True)
        
        # git commit
        subprocess.run(["git", "commit", "-m", message], check=True)
        
        # git push
        subprocess.run(["git", "push"], check=True)
        
        log("✅ 已推送到 GitHub", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Git 推送失败: {e}", "ERROR")
        return False


# ============================================================================
# 通知
# ============================================================================

def send_to_telegram(message: str, file_path: str = None):
    """发送到 Telegram"""
    log("📲 发送到 Telegram...")
    
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    cmd = ["curl", "-s", "-X", "POST",
           "-H", "Content-Type: application/json",
           "-d", json.dumps(data),
           url]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log("✅ 已发送到 Telegram", "SUCCESS")
    else:
        log(f"❌ Telegram 发送失败: {result.stderr}", "ERROR")


def send_to_feishu(title: str, summary: str, url: str):
    """发送到飞书群"""
    log("📲 发送到飞书...")
    
    message = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"📰 **{title}**",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "content": f"{summary}\n\n🔗 [查看详情]({url})",
                        "tag": "lark_md"
                    }
                }
            ]
        }
    }
    
    cmd = ["curl", "-s", "-X", "POST",
           "-H", "Content-Type: application/json",
           "-d", json.dumps(message),
           FEISHU_WEBHOOK]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log("✅ 已发送到飞书", "SUCCESS")
    else:
        log(f"❌ 飞书发送失败: {result.stderr}", "ERROR")


# ============================================================================
# 主流程
# ============================================================================

def main():
    """主函数"""
    log("=" * 60)
    log("🚀 AI Daily Report 开始执行")
    log("=" * 60)
    
    # 1. 抓取所有信息源
    twitter_items = fetch_twitter()
    rss_items = fetch_rss()
    
    if not twitter_items and not rss_items:
        log("❌ 没有任何内容，退出", "ERROR")
        return 1
    
    # 2. 合并内容
    all_content = {
        "twitter": twitter_items,
        "rss": rss_items,
        "total": len(twitter_items) + len(rss_items)
    }
    
    log(f"📊 共收集 {all_content['total']} 条内容")
    
    # 3. 小诸葛分析
    analysis = call_researcher_for_analysis(json.dumps(all_content, ensure_ascii=False))
    
    title = analysis.get("title", f"AI 日报 - {datetime.now().strftime('%Y-%m-%d')}")
    slug = analysis.get("slug", f"daily-{datetime.now().strftime('%Y-%m-%d-%H%M')}")
    
    log(f"📝 标题: {title}")
    log(f"🔗 Slug: {slug}")
    
    # 4. 生成 HTML
    # TODO: 需要修改 html_generator.py 支持自定义 slug
    # html_path = generate_html(analysis, slug)
    
    # 5. Git 推送
    # git_push(html_path, f"添加日报: {title}")
    
    # 6. 发送通知
    # github_pages_url = f"https://maoruibin.github.io/ai-daily-skill/{slug}.html"
    # send_to_telegram(f"📰 {title}\n\n{github_pages_url}")
    # send_to_feishu(title, "新的 AI 日报已生成", github_pages_url)
    
    log("=" * 60)
    log("🎉 完成！", "SUCCESS")
    log("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
