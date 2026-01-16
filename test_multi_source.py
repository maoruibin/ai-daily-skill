#!/usr/bin/env python3
"""
多源 RSS 抓取测试脚本
只测试 RSS 获取功能，不调用 Claude API
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import RSS_SOURCES, KEYWORDS
from src.rss_fetcher import RSSFetcher


def print_banner():
    print("=" * 60)
    print("  多源 RSS 抓取测试")
    print("=" * 60)
    print()


def test_multi_source_fetch():
    """测试多源并行抓取"""
    print(f"配置的 RSS 源数量: {len(RSS_SOURCES)}")
    print(f"关键词过滤: {', '.join(KEYWORDS[:5])}{'...' if len(KEYWORDS) > 5 else ''}")
    print()

    fetcher = RSSFetcher()

    # 1. 测试并行抓取
    print("[步骤 1] 并行抓取所有 RSS 源...")
    print("-" * 60)
    feeds = fetcher.fetch_multiple()
    print()

    if not feeds:
        print("❌ 没有成功抓取任何源")
        return False

    # 2. 测试合并去重
    print("[步骤 2] 合并去重所有条目...")
    print("-" * 60)
    all_entries = fetcher.get_all_entries_from_sources()
    print()

    # 3. 测试关键词过滤
    print("[步骤 3] 关键词过滤...")
    print("-" * 60)
    filtered = fetcher.filter_by_keywords(all_entries)
    print()

    # 4. 显示前几条结果
    print("[步骤 4] 前 5 条匹配的资讯:")
    print("-" * 60)
    for i, entry in enumerate(filtered[:5], 1):
        title = entry.get('title', '无标题')[:60]
        source = getattr(entry, '_source', '未知')
        print(f"{i}. [{source}] {title}")

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            print(f"   时间: {dt}")
        print()

    # 5. 测试日期查找
    print("[步骤 5] 查找今天的资讯...")
    print("-" * 60)
    today = (datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    matched = fetcher.get_content_by_date_from_sources(today)

    if matched:
        print(f"✅ 今天找到 {len(matched)} 条资讯")
        for i, entry in enumerate(matched[:3], 1):
            title = entry.get('title', '无标题')[:50]
            print(f"   {i}. {title}")
    else:
        print(f"   今天 ({today}) 暂无资讯")

    print()
    print("=" * 60)
    print("  测试完成!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    print_banner()
    test_multi_source_fetch()
