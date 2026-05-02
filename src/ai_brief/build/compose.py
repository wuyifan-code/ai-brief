"""早报文章生成模块"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI


def clean_response(text: str) -> str:
    """清理LLM输出中的思考内容，只保留正文"""
    import re
    # 移除 ANSI escape sequences
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    # 移除 <think>...[/CONTENT] 整块
    text = re.sub(r'<think>[\s\S]*?\[/CONTENT\]', '', text)
    # 移除任何剩余的 <think> 块
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    # 取第一行非空且不以特殊标记开头的内容
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        if not line.startswith('# ') and not line.startswith('**'):
            return line
    return text.strip() if text.strip() else ""


class BriefComposer:
    """早报生成器"""

    def __init__(self, openai_config: dict[str, str], config: dict[str, Any]):
        self.config = config
        self.ai_config = config.get("ai", {})
        self.summary_length = self.ai_config.get("summary_length", 50)
        self.openai_config = openai_config

        # 如果没有 API key，使用规则生成
        self.use_llm = bool(openai_config.get("api_key"))

        if self.use_llm:
            self.client = OpenAI(
                base_url=openai_config["base_url"],
                api_key=openai_config["api_key"],
            )
            self.model = openai_config["model_writer"]

    def compose(self, items: list[dict[str, Any]], date: str) -> str:
        """生成早报 Markdown"""
        if not items:
            return self._empty_brief(date)

        # 生成期号
        issue_no = self._generate_issue_no(date)

        # 生成标题
        title = self._generate_title(items, date)

        # 生成今日要闻
        highlights = self._generate_highlights(items)

        # 生成目录
        toc = self._generate_toc(items)

        # 生成正文
        content = self._generate_content(items)

        # 组装完整 Markdown
        brief = f"""# {title}
> {issue_no} | {date}

---

## 今日要闻

{highlights}

---

## 目录

{toc}

---

{content}

---

## 资讯来源

"""
        # 添加来源列表
        sources = self._extract_sources(items)
        for source in sources:
            brief += f"- [{source['name']}]({source['url']})\n"

        brief += f"""
> 本早报由 AI 自动生成 | 更新日期: {date}
"""
        return brief

    def _empty_brief(self, date: str) -> str:
        """空早报"""
        return f"""# AI 早报 {date}

暂无内容。

> 本早报由 AI 自动生成 | 更新日期: {date}
"""

    def _generate_issue_no(self, date: str) -> str:
        """生成期号"""
        # 计算从2024-01-01到现在的天数作为期号
        from datetime import datetime
        start_date = datetime(2024, 1, 1)
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        days = (date_obj - start_date).days
        return f"第{days}期"

    def _generate_highlights(self, items: list[dict[str, Any]]) -> str:
        """生成今日要闻（3条最重要新闻的简要）"""
        if not items:
            return "暂无重要新闻"
        highlights = []
        for i, item in enumerate(items[:3], 1):
            title = item.get("title", "")[:40]
            score = item.get("score", 0)
            highlights.append(f"{i}. **{title}** ⭐{score}")
        return "\n".join(highlights)

    def _generate_title(self, items: list[dict[str, Any]], date: str) -> str:
        """生成早报标题 - 使用规则方式"""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = date_obj.strftime("%Y年%m月%d日")

        # 获取最重要的一条新闻作为参考
        top_news = items[0] if items else {}
        top_title = top_news.get('title', '')

        # 规则方式：从标题提取关键词或使用固定格式
        if 'GPT' in top_title or 'OpenAI' in top_title:
            return f"GPT新时代 | {date_str}"
        elif 'NVIDIA' in top_title or 'GeForce' in top_title:
            return f"GPU算力新时代 | {date_str}"
        elif '云' in top_title or 'Cloud' in top_title:
            return f"云AI爆发 | {date_str}"
        elif '开源' in top_title or 'OpenClaw' in top_title:
            return f"开源AI崛起 | {date_str}"
        elif 'Agent' in top_title or '代理' in top_title:
            return f"AI Agent进化 | {date_str}"
        else:
            return f"AI速递 | {date_str}"

    def _generate_toc(self, items: list[dict[str, Any]]) -> str:
        """生成目录"""
        toc_entries = []
        for i, item in enumerate(items, 1):
            title = item.get("title", "")[:35]
            topic = item.get("topic", "")
            topic_str = f" [{topic}]" if topic else ""
            toc_entries.append(f"{i:02d}. [{title}](#{i:02d}-title){topic_str}")
        return "\n".join(toc_entries)

    def _generate_content(self, items: list[dict[str, Any]]) -> str:
        """生成正文内容"""
        content = ""
        for i, item in enumerate(items, 1):
            title = item.get("title", "")
            summary = item.get("summary", "")
            keywords = item.get("keywords", [])
            link = item.get("link", "")
            source = item.get("source", "")
            score = item.get("score", 0)
            topic = item.get("topic", "")
            related_news = item.get("related_news", [])

            # 清理摘要中的HTML标签和实体
            summary = self._clean_html(summary)

            # 编号标题（如 01、02）
            content += f"## {i:02d} {title}\n\n"

            # 评分星级
            stars = "★" * min(score, 5)
            content += f"{stars} {score}/10\n\n"

            # 摘要正文
            content += f"{summary}\n\n"

            # 主题标签（如果有）
            if topic:
                content += f"[{topic}]\n\n"

            # 关键词标签
            if keywords:
                kw_tags = " ".join(f"#{kw}" for kw in keywords[:5])
                content += f"{kw_tags}\n\n"

            # 关联新闻（如果有）
            if related_news:
                content += "**相关阅读**:\n"
                for news in related_news[:2]:
                    news_title = news.get('title', '')[:45]
                    news_link = news.get('link', '')
                    content += f"- [{news_title}]({news_link})\n"
                content += "\n"

            # 来源链接
            content += f"[原文链接]({link})\n\n"

            # 分隔线
            content += "---\n\n"

        return content

    def _clean_html(self, text: str) -> str:
        """清理HTML标签和实体"""
        import re
        # 清理HTML实体
        text = text.replace('&#8217;', "'").replace('&#38;', "&").replace('&#8230;', "...").replace('&amp;', "&")
        text = text.replace('[&#8230;]', "...").replace('[...]', "...")
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        # 截取前200字
        if len(text) > 200:
            text = text[:200] + "..."
        return text.strip()

    def _extract_sources(self, items: list[dict[str, Any]]) -> list[dict[str, str]]:
        """提取唯一来源"""
        sources_map: dict[str, dict[str, str]] = {}
        for item in items:
            source = item.get("source", "")
            source_url = item.get("source_url", "")
            if source and source not in sources_map:
                sources_map[source] = {"name": source, "url": source_url}

        return list(sources_map.values())

    def save(self, date: str, content: str) -> Path:
        """保存早报"""
        output_path = Path(f"content/daily/{date}.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
