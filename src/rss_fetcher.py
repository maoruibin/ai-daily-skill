"""
RSS 获取与解析模块
负责下载 RSS XML 并解析出目标日期的内容
支持多源并行抓取和关键词过滤
"""
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dateutil import parser as date_parser
import re
import concurrent.futures

from src.config import RSS_URL, RSS_SOURCES, RSS_TIMEOUT, KEYWORDS


class RSSFetcher:
    """RSS 获取器 - 支持多源并行抓取"""

    def __init__(self, rss_url: str = None, rss_sources: List[str] = None):
        # 优先使用传入的单个 URL，否则使用多源配置
        self.rss_url = rss_url or RSS_URL
        self.rss_sources = rss_sources or RSS_SOURCES
        self.timeout = RSS_TIMEOUT
        self._feed_data = None
        self._all_feeds = []  # 存储多个源的数据

    def fetch(self) -> feedparser.FeedParserDict:
        """下载并解析 RSS"""
        print(f"📥 正在下载 RSS: {self.rss_url}")

        try:
            response = requests.get(
                self.rss_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Daily/1.0)"
                }
            )
            response.raise_for_status()

            # 使用 feedparser 解析
            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"⚠️ RSS 解析警告: {feed.bozo_exception}")

            print(f"✅ RSS 下载成功，共 {len(feed.entries)} 条资讯")
            self._feed_data = feed
            return feed

        except requests.RequestException as e:
            raise Exception(f"RSS 下载失败: {e}")
        except Exception as e:
            raise Exception(f"RSS 解析失败: {e}")

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """获取所有条目"""
        if not self._feed_data:
            self.fetch()
        return self._feed_data.entries

    def get_content_by_date(self, target_date: str, feed: feedparser.FeedParserDict = None) -> Optional[Dict[str, Any]]:
        """
        根据日期获取资讯内容

        Args:
            target_date: 目标日期，格式: YYYY-MM-DD
            feed: RSS 数据，如果为空则重新获取

        Returns:
            匹配的条目，如果没有找到则返回 None
        """
        if feed is None:
            feed = self.fetch()

        # 解析目标日期
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"日期格式错误: {target_date}，期望格式: YYYY-MM-DD")

        print(f"🔍 正在查找日期: {target_date}")

        # 尝试多种方式匹配日期
        for entry in feed.entries:
            # 方法1: 检查 pubDate
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if self._is_same_day(pub_dt, target_dt):
                    return self._extract_entry_content(entry)

            # 方法2: 从 link 中提取日期 (格式: .../issues/YY-MM-DD-slug/)
            if hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link and date_from_link == target_date:
                    return self._extract_entry_content(entry)

        print(f"❌ 未找到日期 {target_date} 的资讯")
        return None

    def _is_same_day(self, dt1: datetime, dt2: datetime) -> bool:
        """判断两个日期是否是同一天"""
        return (dt1.year, dt1.month, dt1.day) == (dt2.year, dt2.month, dt2.day)

    def _extract_date_from_link(self, link: str) -> Optional[str]:
        """从链接中提取日期，格式: YY-MM-DD 或 YYYY-MM-DD"""
        # 匹配 /issues/26-01-13- 或 /issues/2026-01-13- 格式
        patterns = [
            r'/issues/(\d{2})-(\d{2})-(\d{2})-',  # YY-MM-DD
            r'/issues/(\d{4})-(\d{2})-(\d{2})-',  # YYYY-MM-DD
        ]

        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                year, month, day = match.groups()
                # 如果是两位年份，转换为四位
                if len(year) == 2:
                    year = "20" + year
                return f"{year}-{month}-{day}"

        return None

    def _extract_entry_content(self, entry) -> Dict[str, Any]:
        """提取条目内容"""
        content = {
            "title": "",
            "link": "",
            "guid": "",
            "description": "",
            "content": "",
            "pubDate": ""
        }

        # 提取标题
        content["title"] = entry.get("title", "")

        # 提取链接
        content["link"] = entry.get("link", "")

        # 提取 GUID
        content["guid"] = entry.get("id", entry.get("guid", content["link"]))

        # 提取描述
        content["description"] = entry.get("description", "")

        # 提取完整内容
        if hasattr(entry, 'content') and entry.content:
            content["content"] = entry.content[0].get('value', '')
        elif hasattr(entry, 'summary'):
            content["content"] = entry.summary
        else:
            content["content"] = content["description"]

        # 提取发布日期
        if hasattr(entry, 'published'):
            content["pubDate"] = entry.published
        elif hasattr(entry, 'updated'):
            content["pubDate"] = entry.updated

        # 清理 HTML 实体
        content["content"] = content["content"].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        return content

    def get_latest_date(self, feed: feedparser.FeedParserDict = None) -> Optional[str]:
        """获取最新的资讯日期"""
        if feed is None:
            feed = self.fetch()

        if not feed.entries:
            return None

        # 获取第一条的日期
        entry = feed.entries[0]

        # 尝试从 link 中提取
        if hasattr(entry, 'link'):
            date_from_link = self._extract_date_from_link(entry.link)
            if date_from_link:
                return date_from_link

        # 尝试从 pubDate 中提取
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d")

        return None

    def get_date_range(self, feed: feedparser.FeedParserDict = None) -> tuple:
        """获取 RSS 中的日期范围"""
        if feed is None:
            feed = self.fetch()

        if not feed.entries:
            return None, None

        dates = []
        for entry in feed.entries:
            if hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link:
                    dates.append(date_from_link)

        if not dates:
            return None, None

        return min(dates), max(dates)

    # ============================================================================
    # 多源并行抓取功能
    # ============================================================================

    def fetch_multiple(self) -> List[feedparser.FeedParserDict]:
        """
        并行抓取多个 RSS 源

        Returns:
            成功抓取的 feed 列表
        """
        # 如果设置了单个 URL，使用旧逻辑
        if self.rss_url:
            feed = self.fetch()
            return [feed] if feed else []

        print(f"📥 正在并行抓取 {len(self.rss_sources)} 个 RSS 源...")
        print(f"   源列表: {self.rss_sources}")
        print()

        successful_feeds = []
        failed_sources = []

        # 使用线程池并行抓取
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有抓取任务
            future_to_url = {
                executor.submit(self._fetch_single, url): url
                for url in self.rss_sources
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    feed = future.result()
                    if feed and feed.entries:
                        successful_feeds.append(feed)
                        print(f"   ✅ {url[:50]}... ({len(feed.entries)} 条)")
                    else:
                        failed_sources.append(url)
                        print(f"   ⚠️ {url[:50]}... (无内容)")
                except Exception as e:
                    failed_sources.append(url)
                    print(f"   ❌ {url[:50]}... ({str(e)[:30]})")

        print()
        print(f"✅ 成功抓取 {len(successful_feeds)} 个源")

        if failed_sources:
            print(f"⚠️ 失败 {len(failed_sources)} 个源")

        self._all_feeds = successful_feeds
        return successful_feeds

    def _fetch_single(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """抓取单个 RSS 源"""
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Daily/1.0)"
                }
            )
            response.raise_for_status()
            return feedparser.parse(response.content)
        except Exception:
            return None

    def get_all_entries_from_sources(self) -> List[Dict[str, Any]]:
        """
        从所有源获取所有条目，去重并排序

        Returns:
            合并后的所有条目列表
        """
        if not self._all_feeds:
            self.fetch_multiple()

        # 使用 URL 去重
        seen_urls = set()
        all_entries = []

        for feed in self._all_feeds:
            for entry in feed.entries:
                url = entry.get('link', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    # 添加来源信息
                    entry._source = getattr(feed, 'feed', {}).get('title', url)
                    all_entries.append(entry)

        # 按时间排序（最新的在前）
        all_entries.sort(
            key=lambda e: e.get('published_parsed', (0, 0, 0, 0, 0, 0, 0, 0, 0)),
            reverse=True
        )

        print(f"📊 合并后共 {len(all_entries)} 条不重复资讯")
        return all_entries

    def filter_by_keywords(self, entries: List[Dict[str, Any]], keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        根据关键词过滤条目

        Args:
            entries: 条目列表
            keywords: 关键词列表，默认使用配置中的 KEYWORDS

        Returns:
            过滤后的条目列表
        """
        if keywords is None:
            keywords = KEYWORDS

        # 如果关键词列表为空，返回所有条目
        if not keywords:
            return entries

        filtered = []
        for entry in entries:
            if self._matches_keywords(entry, keywords):
                filtered.append(entry)

        if filtered:
            print(f"🔍 关键词过滤: {len(filtered)}/{len(entries)} 条匹配")

        return filtered

    def _matches_keywords(self, entry: Dict[str, Any], keywords: List[str]) -> bool:
        """检查条目是否匹配任何关键词"""
        # 获取可搜索的文本
        title = entry.get('title', '').lower()
        summary = entry.get('summary', entry.get('description', '')).lower()
        tags = ' '.join(
            tag.get('term', '') for tag in entry.get('tags', [])
        ).lower()

        combined_text = f"{title} {summary} {tags}"

        # 检查是否匹配任何关键词（不区分大小写）
        for keyword in keywords:
            if keyword.lower() in combined_text:
                return True

        return False

    def get_todays_entries(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        获取最近 N 天的条目（来自所有源，带关键词过滤）

        Args:
            days_back: 回溯天数

        Returns:
            匹配的条目列表
        """
        all_entries = self.get_all_entries_from_sources()

        # 应用关键词过滤
        filtered_entries = self.filter_by_keywords(all_entries)

        # 按日期过滤
        target_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        recent_entries = []
        for entry in filtered_entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                entry_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if entry_date >= cutoff_date:
                    recent_entries.append(entry)

        print(f"📅 最近 {days_back} 天内有 {len(recent_entries)} 条相关资讯")
        return recent_entries

    def get_content_by_date_from_sources(self, target_date: str) -> List[Dict[str, Any]]:
        """
        从所有源获取指定日期的内容

        Args:
            target_date: 目标日期 (YYYY-MM-DD)

        Returns:
            匹配的所有条目列表
        """
        all_entries = self.get_all_entries_from_sources()

        # 应用关键词过滤
        filtered_entries = self.filter_by_keywords(all_entries)

        # 解析目标日期
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"日期格式错误: {target_date}")

        # 查找匹配日期的条目
        matched_entries = []
        for entry in filtered_entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if self._is_same_day(pub_dt, target_dt):
                    matched_entries.append(entry)

        print(f"📅 {target_date} 找到 {len(matched_entries)} 条相关资讯")
        return matched_entries


def fetch_rss_content(target_date: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定日期的 RSS 内容"""
    fetcher = RSSFetcher()
    feed = fetcher.fetch()
    return fetcher.get_content_by_date(target_date, feed)
