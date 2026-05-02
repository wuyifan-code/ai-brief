"""RSS Feed 生成模块"""

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class RSSGenerator:
    """RSS Feed 生成器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.publishing_config = config.get("publishing", {})
        self.site_dir = Path("site")
        self.site_dir.mkdir(exist_ok=True)

    def generate(self, date: str, brief_path: Path) -> Path:
        """生成 RSS Feed"""
        brief_content = brief_path.read_text(encoding="utf-8")

        # 解析早报内容
        items = self._parse_items(brief_content, date)

        # 生成 RSS XML
        rss_xml = self._render_rss(items, date)

        # 写入文件
        rss_path = self.site_dir / "feed.xml"
        rss_path.write_text(rss_xml, encoding="utf-8")

        return rss_path

    def _parse_items(self, content: str, date: str) -> list[dict[str, str]]:
        """解析早报内容为 RSS 项"""
        items = []

        import re

        # 提取新闻标题和链接
        pattern = r"### \d+\. (.+?)\n\n.+?\n\n.+?\n+?\*\*来源\*\*: \[.+?\]\((.+?)\)"

        matches = re.findall(pattern, content, re.DOTALL)
        for title, link in matches:
            items.append(
                {
                    "title": title.strip(),
                    "link": link.strip(),
                    "description": self._extract_summary(content, title),
                    "pub_date": f"{date} 08:00:00 +0800",
                }
            )

        return items

    def _extract_summary(self, content: str, title: str) -> str:
        """提取摘要"""
        import re

        pattern = rf"### \d+\. {re.escape(title)}\n\n.+?\n\n(.+?)\n\n"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # 清理 markdown
            summary = re.sub(r"\*\*([^*]+)\*\*", r"\1", summary)
            return summary[:200]
        return ""

    def _render_rss(self, items: list[dict[str, str]], date: str) -> str:
        """渲染 RSS XML"""
        title = self.publishing_config.get("title", "AI 早报")
        description = self.publishing_config.get("description", "每日 AI 资讯精选")
        base_url = self.publishing_config.get("base_url", "https://example.com")

        build_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

        rss_items = ""
        for item in items:
            rss_items += f"""    <item>
        <title><![CDATA[{item['title']}]]></title>
        <link>{item['link']}</link>
        <description><![CDATA[{item['description']}]]></description>
        <pubDate>{item['pub_date']}</pubDate>
    </item>
"""

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{title}</title>
        <link>{base_url}</link>
        <description>{description}</description>
        <language>zh-cn</language>
        <lastBuildDate>{build_date}</lastBuildDate>
        <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>
{rss_items}
    </channel>
</rss>
"""

    def validate_feed(self, rss_path: Path) -> bool:
        """验证 RSS Feed 有效性"""
        if not rss_path.exists():
            return False

        content = rss_path.read_text(encoding="utf-8")

        # 基本验证
        required_elements = ["<rss", "<channel>", "<title>", "<link>", "</channel>", "</rss>"]
        return all(elem in content for elem in required_elements)
