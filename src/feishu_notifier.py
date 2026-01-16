"""
飞书通知模块
通过 Webhook 发送消息到飞书群
"""
import os
import json
import requests
from datetime import datetime
from typing import Optional


class FeishuNotifier:
    """飞书 Webhook 通知器"""

    def __init__(self, webhook_url: str = None):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书群机器人 Webhook 地址
        """
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")

    def _is_configured(self) -> bool:
        """检查 Webhook 是否已配置"""
        return bool(self.webhook_url)

    def send_news(self, title: str, content: str, url: str = None) -> bool:
        """
        发送资讯到飞书群

        Args:
            title: 标题
            content: 内容（支持 Markdown）
            url: 可选的链接地址

        Returns:
            是否发送成功
        """
        if not self._is_configured():
            print("⚠️ 飞书 Webhook 未配置，跳过发送")
            return False

        # 构建飞书消息卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "orange"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
            }
        }

        # 添加链接按钮
        if url:
            card["card"]["elements"].append({
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "查看完整日报"
                    },
                    "type": "default",
                    "url": url
                }]
            })

        # 添加时间戳
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "style": {
                    "font_size": "extra_small",
                    "color": "gray"
                }
            }
        })

        try:
            response = requests.post(
                self.webhook_url,
                json=card,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                print(f"✅ 飞书消息已发送")
                return True
            else:
                print(f"❌ 飞书发送失败: {result}")
                return False

        except Exception as e:
            print(f"❌ 飞书发送异常: {e}")
            return False

    def send_summary(
        self,
        date: str,
        summary: list,
        keywords: list = None,
        page_url: str = None
    ) -> bool:
        """
        发送 AI 日报摘要

        Args:
            date: 日期
            summary: 摘要列表
            keywords: 关键词列表
            page_url: 网页链接

        Returns:
            是否发送成功
        """
        # 构建内容
        content_lines = [f"**📅 {date}**\n"]

        if summary:
            content_lines.append("**核心摘要**\n")
            for i, item in enumerate(summary[:5], 1):
                content_lines.append(f"{i}. {item}\n")

        if keywords:
            content_lines.append(f"\n**关键词**\n{' '.join([f'#{kw}' for kw in keywords[:8]])}")

        content = "".join(content_lines)

        return self.send_news(
            title="🤖 AI Daily 每日资讯",
            content=content,
            url=page_url
        )

    def send_error(self, date: str, error: str) -> bool:
        """发送错误通知"""
        content = f"""**❌ 生成失败**

📅 日期: {date}
🔴 错误: {error}"""

        return self.send_news(
            title="❌ AI Daily 生成失败",
            content=content
        )

    def send_empty(self, date: str, reason: str = "") -> bool:
        """发送空数据通知"""
        content = f"""**📭 今日暂无资讯**

📅 日期: {date}
💡 原因: {reason or "RSS中未找到对应日期的资讯"}"""

        return self.send_news(
            title="📭 AI Daily 无数据",
            content=content
        )


def send_feishu_news(title: str, content: str, url: str = None) -> bool:
    """便捷函数：发送消息到飞书"""
    notifier = FeishuNotifier()
    return notifier.send_news(title, content, url)
