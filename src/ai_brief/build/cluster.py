"""事件聚类模块"""
from collections import defaultdict
from typing import Any
import re


# 主题关键词映射表
TOPIC_KEYWORDS = {
    "LLM/模型": ["LLM", "GPT", "Claude", "Gemini", "DeepSeek", "模型", "大模型", "OpenAI", "Anthropic", "NVIDIA"],
    "开源生态": ["开源", "OpenClaw", "Meta", "Llama", "Mistral"],
    "云游戏": ["云游戏", "GeForce", "NVIDIA", "游戏", "Cloud"],
    "企业AI": ["SAP", "企业", " governance", "治理", "利润", "Copilot", "GitHub"],
    "Agent": ["Agent", "代理", "autonomous", "规划", "工具"],
    "基础设施": ["基础设施", "capex", "云", "Big Tech", "投资"],
    "物理AI": ["Physical AI", "LG", "机器人", "自动化"],
    "API/MCP": ["API", "MCP", "gateway", "网关"],
}


class EventCluster:
    """事件聚类器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def cluster(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """对新闻进行聚类"""
        if not items:
            return []

        # 按主题分组
        topic_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        uncategorized = []

        for item in items:
            topic = self._detect_topic(item)
            if topic:
                topic_groups[topic].append(item)
            else:
                uncategorized.append(item)

        # 合并同类新闻
        merged: list[dict[str, Any]] = []
        for topic, group_items in topic_groups.items():
            if len(group_items) == 1:
                merged.append(group_items[0])
            else:
                # 按分数排序，保留最高分的作为主新闻
                sorted_group = sorted(group_items, key=lambda x: x.get("score", 0), reverse=True)
                primary = sorted_group[0]

                # 合并相关信息
                related = [{
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "source": item.get("source", ""),
                } for item in sorted_group[1:5]]  # 最多保留4条关联新闻

                merged_item = {
                    **primary,
                    "related_news": related,
                    "cluster_size": len(group_items),
                    "topic": topic,
                }
                merged.append(merged_item)

        # 添加未分类的新闻
        for item in uncategorized:
            merged.append(item)

        # 按分数排序
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        return merged

    def _detect_topic(self, item: dict[str, Any]) -> str | None:
        """检测新闻主题"""
        text = f"{item.get('title', '')} {item.get('summary', '')}"

        for topic, keywords in TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    return topic
        return None

    def _merge_cluster(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        """合并聚类中的项目"""
        # 保留分数最高的
        primary = max(items, key=lambda x: x.get("score", 0))

        # 添加被合并的项目信息
        merged_titles = [item.get("title", "") for item in items if item != primary]

        return {
            **primary,
            "related_news": merged_titles,
            "cluster_size": len(items),
        }
