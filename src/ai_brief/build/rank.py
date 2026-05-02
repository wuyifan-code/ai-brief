"""新闻评分模块"""

import json
import re
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


class NewsRanker:
    """新闻评分器"""

    def __init__(self, openai_config: dict[str, str], config: dict[str, Any]):
        self.config = config
        self.ai_config = config.get("ai", {})
        self.threshold = self.ai_config.get("score_threshold", 5)
        self.max_items = self.ai_config.get("max_news_items", 20)
        self.openai_config = openai_config

        # 如果没有 API key，使用规则评分
        self.use_llm = bool(openai_config.get("api_key"))

        if self.use_llm:
            self.client = OpenAI(
                base_url=openai_config["base_url"],
                api_key=openai_config["api_key"],
            )
            self.model = openai_config["model_fast"]

    def rank(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """对新闻进行评分和排序"""
        if not items:
            return []

        # 按权重排序
        sorted_items = sorted(items, key=lambda x: x.get("weight", 0), reverse=True)

        # 生成评分 prompt
        scored_items = []
        for item in sorted_items[: self.max_items * 2]:  # 先多取一些
            score = self._score_item(item)
            item["score"] = score
            item["summary"] = self._generate_summary(item)
            item["keywords"] = self._extract_keywords(item)

            if score >= self.threshold:
                scored_items.append(item)

        # 按分数排序并截取
        scored_items.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_items[: self.max_items]

    def _score_item(self, item: dict[str, Any]) -> int:
        """使用 LLM 评分"""
        if not self.use_llm:
            # 规则评分：使用配置中的权重
            return item.get("weight", 5)

        title = item.get("title", "")
        summary = item.get("summary", "")
        category = item.get("category", "")

        prompt = f"""你是一个专业的AI新闻评分专家。给你的新闻打分(1-10)。
新闻：{title}
类别：{category}

只输出一个数字(1-10)，不要解释。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个评分助手。直接输出数字，不要输出其他内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=5,
                temperature=0.1,
            )
            score_text = clean_response(response.choices[0].message.content)
            score = int("".join(filter(str.isdigit, score_text[:5])))
            return min(max(score, 1), 10)
        except Exception:
            # 降级：使用权重作为分数
            return item.get("weight", 5)

    def _generate_summary(self, item: dict[str, Any]) -> str:
        """生成摘要 - 使用规则方式"""
        title = item.get("title", "")
        summary = item.get("summary", "")

        if summary:
            # 清理HTML实体
            summary = summary.replace('&#8217;', "'").replace('&#38;', "&").replace('&#8230;', "...").replace('&amp;', "&").replace('[&#8230;]', "...").replace('[', "").replace(']', "")
            # 截取前200字
            if len(summary) > 200:
                return summary[:200] + "..."
            return summary
        return title

    def _extract_keywords(self, item: dict[str, Any]) -> list[str]:
        """提取关键词 - 使用规则方式"""
        title = item.get("title", "")
        summary = item.get("summary", "")

        # 规则：从标题和摘要中提取AI相关关键词
        import re
        # 常见AI关键词
        ai_keywords = ["AI", "LLM", "GPT", "Claude", "Gemini", "DeepSeek", "OpenAI", "Meta", "Google", "Microsoft", "NVIDIA", "模型", "大模型", "多模态", "Agent", "Copilot", "RAG", "推理", "训练", "部署", "开源", "发布", "更新", "云游戏", "TTS", "API", "MCP"]
        found = []
        text = f"{title} {summary}"
        for kw in ai_keywords:
            if kw.lower() in text.lower():
                found.append(kw)
        return found[:5] if found else ["AI"]

    def save_ranked(self, date: str, items: list[dict[str, Any]]) -> None:
        """保存评分后的数据"""
        output_path = f"data/processed/{date}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
