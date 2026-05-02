"""HTML 卡片生成模块"""

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def generate_cards(brief_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    """生成 HTML 卡片"""
    # 解析 Markdown 文件
    items = parse_brief(brief_path)

    # 获取视频配置
    video_config = config.get("video", {})
    theme_color = video_config.get("theme_color", "#1a1a2e")
    accent_color = video_config.get("accent_color", "#e94560")
    text_color = video_config.get("text_color", "#ffffff")
    font_family = video_config.get("font_family", "Noto Sans SC, Microsoft YaHei, sans-serif")
    title_font_size = video_config.get("title_font_size", 48)
    body_font_size = video_config.get("body_font_size", 32)
    max_chars = video_config.get("max_chars_per_card", 150)
    width = video_config.get("width", 1920)
    height = video_config.get("height", 1080)

    # 设置 Jinja2 环境
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # 确保默认模板存在
    default_template = template_dir / "card.html"
    if not default_template.exists():
        default_template.write_text(CARD_TEMPLATE, encoding="utf-8")

    template = env.get_template("card.html")

    cards = []
    for i, item in enumerate(items, 1):
        # 截断正文
        body = item.get("body", "")[:max_chars]
        if len(item.get("body", "")) > max_chars:
            body += "..."

        html_content = template.render(
            index=i,
            title=item.get("title", ""),
            body=body,
            source=item.get("source", ""),
            keywords=item.get("keywords", ""),
            score=item.get("score", ""),
            theme_color=theme_color,
            accent_color=accent_color,
            text_color=text_color,
            font_family=font_family,
            title_font_size=title_font_size,
            body_font_size=body_font_size,
            width=width,
            height=height,
        )

        cards.append(
            {
                "index": i,
                "html": html_content,
                "title": item.get("title", ""),
                "body": body,
            }
        )

    return cards


def parse_brief(brief_path: Path) -> list[dict[str, Any]]:
    """解析早报 Markdown 文件"""
    if not brief_path.exists():
        return []

    content = brief_path.read_text(encoding="utf-8")

    # 解析每个新闻条目
    items = []

    # 匹配 ### 标题 格式
    pattern = r"### (\d+)\. (.+?)\n\n\*\*评分\*\*:.+?\((.+?)/10\)\n\n(.+?)\n\n\*\*关键词\*\*: (.+?)\n\n\*\*来源\*\*:"

    matches = re.findall(pattern, content, re.DOTALL)
    for match in matches:
        index, title, score, body, keywords = match
        items.append(
            {
                "title": title.strip(),
                "score": score.strip(),
                "body": body.strip(),
                "keywords": keywords.strip(),
                "source": extract_source_from_brief(content, title),
            }
        )

    return items


def extract_source_from_brief(content: str, title: str) -> str:
    """从早报内容中提取来源"""
    # 查找标题后面的来源行
    pattern = rf"### \d+\. {re.escape(title)}.+?\*\*来源\*\*: \[(.+?)\]"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1)
    return ""


CARD_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={{ width }}, height={{ height }}">
    <title>AI 早报 - 新闻 {{ index }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            width: {{ width }}px;
            height: {{ height }}px;
            background: linear-gradient(135deg, {{ theme_color }} 0%, #16213e 100%);
            font-family: {{ font_family }};
            color: {{ text_color }};
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 60px;
            overflow: hidden;
        }
        .header {
            position: absolute;
            top: 40px;
            left: 60px;
            font-size: 24px;
            opacity: 0.7;
        }
        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            max-width: {{ width - 120 }}px;
        }
        .index {
            font-size: 120px;
            font-weight: bold;
            color: {{ accent_color }};
            opacity: 0.3;
            position: absolute;
            top: 50%;
            right: 60px;
            transform: translateY(-50%);
        }
        h1 {
            font-size: {{ title_font_size }}px;
            font-weight: bold;
            margin-bottom: 30px;
            line-height: 1.3;
        }
        .body {
            font-size: {{ body_font_size }}px;
            line-height: 1.8;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 20px;
            opacity: 0.7;
        }
        .keywords {
            color: {{ accent_color }};
        }
        .score {
            color: {{ accent_color }};
        }
    </style>
</head>
<body>
    <div class="header">AI 早报</div>
    <div class="content">
        <h1>{{ index }}. {{ title }}</h1>
        <p class="body">{{ body }}</p>
        <div class="footer">
            <span class="keywords">{{ keywords }}</span>
            <span class="score">⭐ {{ score }}/10</span>
        </div>
    </div>
    <div class="index">{{ index }}</div>
</body>
</html>
"""
