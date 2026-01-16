#!/usr/bin/env python3
"""
生成今日日报（测试模式 - 跳过 Claude 分析）
直接从 RSS 获取资讯并生成 HTML
"""
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rss_fetcher import RSSFetcher
from src.html_generator import HTMLGenerator


def main():
    print("=" * 60)
    print("  生成今日日报（测试模式）")
    print("=" * 60)
    print()

    # 获取今天的日期
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"目标日期: {today}")
    print()

    # 抓取 RSS
    print("[步骤 1] 抓取多源 RSS...")
    fetcher = RSSFetcher()
    feeds = fetcher.fetch_multiple()
    print()

    # 获取今天的资讯
    print("[步骤 2] 获取今天的资讯...")
    matched_entries = fetcher.get_content_by_date_from_sources(today)
    print()

    if not matched_entries:
        print("今天暂无资讯，尝试获取最近 3 天的资讯...")
        entries_3days = fetcher.get_todays_entries(days_back=3)
        matched_entries = entries_3days[:10] if entries_3days else []
        print(f"找到 {len(matched_entries)} 条最近的资讯")

    if not matched_entries:
        print("❌ 没有找到任何资讯")
        return

    # 构建 Claude 分析结果格式（模拟）
    result = {
        "status": "success",
        "date": today,
        "theme": "blue",
        "summary": [
            f"来自 {len(feeds)} 个 RSS 源的 AI 资讯汇总",
            f"共筛选出 {len(matched_entries)} 条相关资讯",
        ],
        "keywords": ["AI", "Agent", "Skill", "Plugin", "Claude", "Anthropic"],
        "categories": [
            {
                "key": "model",
                "name": "最新资讯",
                "icon": "📰",
                "items": []
            }
        ]
    }

    # 添加资讯条目
    for entry in matched_entries[:20]:
        title = entry.get("title", "无标题")
        summary = entry.get("summary", entry.get("description", ""))[:150]
        url = entry.get("link", "")
        source = getattr(entry, '_source', '未知来源')

        result["categories"][0]["items"].append({
            "title": title,
            "summary": f"{summary}... (来源: {source})",
            "url": url,
            "tags": [source]
        })

    # 添加到摘要
    for i, item in enumerate(result["categories"][0]["items"][:5], 1):
        result["summary"].append(f"{i}. {item['title'][:40]}...")

    print()
    print("[步骤 3] 生成 HTML 页面...")

    # 生成 HTML
    generator = HTMLGenerator()
    generator.generate_css()
    html_path = generator.generate_daily(result)

    print(f"✅ 生成成功: {html_path}")
    print()
    print("=" * 60)
    print(f"  共 {len(matched_entries)} 条资讯")
    print(f"  页面路径: {html_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
