#!/usr/bin/env python3
"""
AI Daily Unified - 统一日报生成器

整合多个信息源：
1. Twitter 推荐流
2. RSS（smol.ai 等）

流程：
1. 抓 Twitter
2. 抓 RSS
3. 小诸葛分析 Twitter 内容
4. Claude 统一分析
5. 生成 HTML（标题作为文件名）
6. Git 推送
"""

import os
import sys
import json
import subprocess
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    ZHIPU_API_KEY,
    OUTPUT_DIR,
    FEISHU_WEBHOOK_URL,
    RSS_SOURCES,
    KEYWORDS,
    THEMES,
    DEFAULT_THEME,
    CATEGORIES
)
from src.rss_fetcher import RSSFetcher
from src.claude_analyzer import ClaudeAnalyzer
from src.html_generator import HTMLGenerator


# ============================================================================
# 配置
# ============================================================================

# Telegram
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8586904098:AAHUTjaiNtUvkqIO7UVSVFuOEFsNl-QVBaM")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "8233389572")

# 小诸葛
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
        "WARN": "⚠️",
        "STEP": "📍"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {msg}")


def chinese_to_slug(text: str) -> str:
    """
    中文标题转英文 slug
    
    TODO: 调用翻译 API
    目前用拼音首字母 + 时间戳
    """
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text)
    text = text.strip()
    
    # 简单处理：取前 30 个字符，加时间戳
    timestamp = datetime.now().strftime("%H%M")
    
    # 如果是中文，用拼音首字母（简化版）
    # TODO: 接入翻译 API
    slug = text[:30].lower().replace(' ', '-')
    slug = re.sub(r'[-]+', '-', slug)
    
    return f"{slug}-{timestamp}"


# ============================================================================
# 信息源 1: Twitter（复用 twitter-digest 技能的输出）
# ============================================================================

TWITTER_REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "twitter"

def fetch_twitter() -> List[Dict]:
    """
    读取 twitter-digest 技能生成的报告
    
    返回推文列表
    """
    log("读取 Twitter 报告...", "STEP")
    
    try:
        # 找到今天的报告
        today = datetime.now().strftime("%Y-%m-%d")
        report_file = TWITTER_REPORTS_DIR / f"{today}.md"
        
        if not report_file.exists():
            # 尝试找最新的报告
            reports = sorted(TWITTER_REPORTS_DIR.glob("*.md"), reverse=True)
            if reports:
                report_file = reports[0]
                log(f"今天的报告不存在，使用最新报告: {report_file.name}")
            else:
                log("没有找到 Twitter 报告，跳过", "WARN")
                return []
        
        # 解析 Markdown 报告
        content = report_file.read_text(encoding='utf-8')
        tweets = parse_twitter_report(content)
        
        log(f"✅ 读取到 {len(tweets)} 条推文", "SUCCESS")
        return tweets
        
    except Exception as e:
        log(f"读取 Twitter 报告失败: {e}", "ERROR")
        return []


def parse_twitter_report(content: str) -> List[Dict]:
    """
    解析 Twitter 报告（支持 Markdown 和 JSON 格式）
    
    返回推文列表
    """
    tweets = []
    
    # 尝试 JSON 格式
    if content.strip().startswith("["):
        try:
            return json.loads(content)
        except:
            pass
    
    # Markdown 格式：按 ### 分割
    sections = content.split("### ")[1:]  # 跳过标题
    
    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        
        title = lines[0].strip()
        
        # 提取内容
        tweet_content = ""
        url = ""
        stats = ""
        comment = ""
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("> "):
                tweet_content += line[2:] + " "
            elif line.startswith("- 🔗 原文:") or line.startswith("- 🔗 原文："):
                url = line.split(":", 1)[1].strip() if ":" in line else ""
                url = line.split("：", 1)[1].strip() if "：" in line else url
            elif line.startswith("- 📊 互动:") or line.startswith("- 📊 互动："):
                stats = line.split(":", 1)[1].strip() if ":" in line else ""
                stats = line.split("：", 1)[1].strip() if "：" in line else stats
            elif line.startswith("- 💬 点评:") or line.startswith("- 💬 点评："):
                comment = line.split(":", 1)[1].strip() if ":" in line else ""
                comment = line.split("：", 1)[1].strip() if "：" in line else comment
        
        if title and tweet_content:
            tweets.append({
                "title": title,
                "content": tweet_content.strip(),
                "url": url,
                "stats": stats,
                "comment": comment
            })
    
    return tweets


# ============================================================================
# 信息源 2: RSS
# ============================================================================

def fetch_rss(target_date: str) -> Dict[str, Any]:
    """
    抓取 RSS 源
    
    返回合并后的内容
    """
    log("抓取 RSS 源...", "STEP")
    
    fetcher = RSSFetcher()
    
    # 多源模式
    feeds = fetcher.fetch_multiple()
    all_entries = fetcher.get_all_entries_from_sources()
    filtered_entries = fetcher.filter_by_keywords(all_entries)
    
    # 按日期过滤
    matched_entries = fetcher.get_content_by_date_from_sources(target_date)
    
    if not matched_entries:
        log(f"⚠️  {target_date} 没有 RSS 内容", "WARN")
        return None
    
    # 合并内容
    content_parts = []
    for i, entry in enumerate(matched_entries[:20], 1):
        title = entry.get("title", "无标题")
        link = entry.get("link", "")
        summary = entry.get("summary", entry.get("description", ""))[:500]
        source = getattr(entry, '_source', '未知来源')
        
        content_parts.append(f"""
## {i}. {title}

**来源**: {source}
**链接**: {link}

{summary}

---
""")
    
    merged_content = {
        "title": f"AI 资讯日报 - {target_date}",
        "link": matched_entries[0].get("link", ""),
        "guid": f"daily-{target_date}",
        "description": f"来自 {len(matched_entries)} 个源的 AI 资讯汇总",
        "content": "\n".join(content_parts),
        "pubDate": target_date
    }
    
    log(f"抓取到 {len(matched_entries)} 条 RSS 资讯", "SUCCESS")
    return merged_content


# ============================================================================
# 小诸葛分析
# ============================================================================

def call_researcher(twitter_items: List[Dict]) -> Dict[str, Any]:
    """
    调用小诸葛分析 Twitter 内容
    
    返回：
    {
        "title": "主标题",
        "insights": ["洞察1", "洞察2"],
        "topics": ["话题1", "话题2"]
    }
    """
    if not twitter_items:
        return {
            "title": None,
            "insights": [],
            "topics": []
        }
    
    log("小诸葛分析 Twitter 内容...", "STEP")
    
    # TODO: 使用 sessions_send 调用小诸葛
    # 目前返回空
    log("⚠️  小诸葛调用暂未实现", "WARN")
    
    return {
        "title": None,
        "insights": [],
        "topics": []
    }


# ============================================================================
# 生成标题和 Slug
# ============================================================================

def generate_title_and_slug(analysis_result: Dict, researcher_result: Dict) -> tuple:
    """
    生成标题和 URL slug
    
    Returns:
        (title, slug)
    """
    # 优先用小诸葛生成的标题
    title = researcher_result.get("title")
    
    if not title:
        # 从分析结果中生成
        summary = analysis_result.get("summary", [])
        if summary:
            # 取第一条摘要作为标题基础
            first_summary = summary[0][:50]
            title = f"AI 日报 - {first_summary}"
        else:
            title = f"AI 日报 - {analysis_result.get('date', datetime.now().strftime('%Y-%m-%d'))}"
    
    # 生成 slug
    slug = chinese_to_slug(title)
    
    return title, slug


# ============================================================================
# 修改 HTML 生成器支持自定义文件名
# ============================================================================

def generate_html_with_slug(result: Dict, slug: str) -> str:
    """
    生成 HTML，使用自定义 slug 作为文件名
    """
    generator = HTMLGenerator()
    generator.generate_css()
    
    # 生成 HTML 内容
    date = result.get("date", datetime.now().strftime("%Y-%m-%d"))
    theme_name = result.get("theme", "blue")
    theme = THEMES.get(theme_name, THEMES["blue"])
    
    html_content = generator._build_daily_html(result, theme)
    
    # 使用 slug 作为文件名
    filename = f"{slug}.html"
    filepath = DOCS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log(f"HTML 已生成: {filepath}", "SUCCESS")
    
    # 更新索引
    generator.update_index(date, result)
    
    return str(filepath)


# ============================================================================
# Git 推送
# ============================================================================

def git_push(commit_message: str):
    """推送到 GitHub"""
    log("推送到 GitHub...", "STEP")
    
    try:
        os.chdir(PROJECT_ROOT)
        
        # git add
        result = subprocess.run(["git", "add", "docs/"], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"git add 失败: {result.stderr}", "WARN")
        
        # git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log(f"git commit 失败: {result.stderr}", "WARN")
            # 可能是没有任何变更
            return True
        
        # git push
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"git push 失败: {result.stderr}", "ERROR")
            return False
        
        log("已推送到 GitHub", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Git 操作失败: {e}", "ERROR")
        return False


# ============================================================================
# 通知
# ============================================================================

def send_notification(title: str, slug: str, summary: List[str]):
    """发送通知到 TG 和飞书"""
    
    # GitHub Pages URL
    site_url = os.getenv("SITE_URL", "https://maoruibin.github.io/ai-daily-skill")
    page_url = f"{site_url}/{slug}.html"
    
    # 发送到 Telegram
    log("发送到 Telegram...", "STEP")
    message = f"📰 *{title}*\n\n"
    message += "\n".join([f"• {s}" for s in summary[:5]])
    message += f"\n\n🔗 [查看详情]({page_url})"
    
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
        log("已发送到 Telegram", "SUCCESS")
    
    # 发送到飞书
    if FEISHU_WEBHOOK_URL:
        log("发送到飞书...", "STEP")
        
        feishu_message = {
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
                            "content": "\n".join([f"• {s}" for s in summary[:3]]),
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"content": "查看详情", "tag": "plain_text"},
                                "url": page_url,
                                "type": "primary"
                            }
                        ]
                    }
                ]
            }
        }
        
        cmd = ["curl", "-s", "-X", "POST",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(feishu_message),
               FEISHU_WEBHOOK_URL]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log("已发送到飞书", "SUCCESS")


# ============================================================================
# 主流程
# ============================================================================

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 AI Daily Unified - 统一日报生成器")
    print("=" * 60 + "\n")
    
    # 检查环境
    if not ZHIPU_API_KEY:
        log("错误: ZHIPU_API_KEY 未设置", "ERROR")
        return 1
    
    try:
        # 1. 计算目标日期（前两天）
        target_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        log(f"目标日期: {target_date}")
        
        # 2. 抓取 Twitter
        twitter_items = fetch_twitter()
        
        # 3. 抓取 RSS
        rss_content = fetch_rss(target_date)
        
        if not twitter_items and not rss_content:
            log("没有任何内容，退出", "ERROR")
            return 1
        
        # 4. 小诸葛分析 Twitter
        researcher_result = call_researcher(twitter_items)
        
        # 5. Claude 统一分析
        log("Claude 分析内容...", "STEP")
        analyzer = ClaudeAnalyzer()
        
        # 合并内容
        if rss_content:
            analysis_result = analyzer.analyze(rss_content, target_date)
        else:
            # TODO: 处理 Twitter 内容
            log("只有 Twitter 内容，暂不支持", "WARN")
            return 1
        
        if analysis_result.get("status") == "empty":
            log("分析结果为空", "WARN")
            return 0
        
        # 6. 生成标题和 slug
        title, slug = generate_title_and_slug(analysis_result, researcher_result)
        log(f"标题: {title}")
        log(f"Slug: {slug}")
        
        # 7. 生成 HTML
        html_path = generate_html_with_slug(analysis_result, slug)
        
        # 8. Git 推送
        git_push(f"添加日报: {title}")
        
        # 9. 发送通知
        summary = analysis_result.get("summary", [])
        send_notification(title, slug, summary)
        
        print("\n" + "=" * 60)
        log("🎉 完成！", "SUCCESS")
        print("=" * 60 + "\n")
        
        return 0
        
    except Exception as e:
        log(f"执行失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
