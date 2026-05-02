"""静态站点生成模块"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class SiteGenerator:
    """静态站点生成器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.publishing_config = config.get("publishing", {})
        self.site_dir = Path("site")
        self.site_dir.mkdir(exist_ok=True)

    def generate(self, date: str, brief_path: Path) -> Path:
        """生成静态站点"""
        # 读取早报内容
        brief_content = brief_path.read_text(encoding="utf-8")

        # 获取所有早报列表
        briefs = self._get_briefs_list()

        # 生成首页
        index_html = self._render_index(date, brief_content, briefs)
        index_path = self._write_file("index.html", index_html)

        # 复制每日早报
        daily_dir = self._write_file(f"daily/{date}.md", brief_content)

        # 生成 CSS
        self._generate_css()

        return index_path

    def _get_briefs_list(self) -> list[dict[str, str]]:
        """获取早报列表"""
        briefs = []
        content_dir = Path("content/daily")

        if content_dir.exists():
            for md_file in sorted(content_dir.glob("*.md"), reverse=True):
                date = md_file.stem
                # 提取标题
                title = "AI 早报"
                content = md_file.read_text(encoding="utf-8")
                import re

                title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1)

                briefs.append({"date": date, "title": title, "path": f"daily/{date}.md"})

        return briefs[:30]  # 最多显示30条

    def _render_index(self, date: str, brief_content: str, briefs: list[dict[str, str]]) -> str:
        """渲染首页"""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)

        # 确保默认模板存在
        index_template = template_dir / "index.html"
        if not index_template.exists():
            index_template.write_text(INDEX_TEMPLATE, encoding="utf-8")

        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("index.html")

        title = self.publishing_config.get("title", "AI 早报")
        subtitle = self.publishing_config.get("subtitle", "每日 AI 资讯精选")

        return template.render(
            title=title,
            subtitle=subtitle,
            current_date=date,
            brief_content=brief_content,
            briefs=briefs,
        )

    def _write_file(self, relative_path: str, content: str) -> Path:
        """写入文件"""
        file_path = self.site_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def _generate_css(self) -> None:
        """生成 CSS 文件"""
        css_content = """/* AI 早报静态站点样式 */
:root {
    --theme-color: #1a1a2e;
    --accent-color: #e94560;
    --text-color: #333;
    --bg-color: #f5f5f5;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background: var(--bg-color);
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: var(--theme-color);
    color: white;
    padding: 40px 20px;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
}

header .subtitle {
    opacity: 0.8;
}

main {
    background: white;
    padding: 40px;
    margin: 20px 0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.brief-content {
    font-size: 1.1rem;
}

.brief-content h1 {
    font-size: 2rem;
    margin-bottom: 20px;
    color: var(--theme-color);
}

.brief-content h2 {
    margin-top: 30px;
    margin-bottom: 15px;
    color: var(--theme-color);
}

.brief-content h3 {
    margin-top: 25px;
    margin-bottom: 10px;
    color: var(--theme-color);
}

.brief-content ul {
    padding-left: 20px;
}

.brief-content a {
    color: var(--accent-color);
    text-decoration: none;
}

.brief-content a:hover {
    text-decoration: underline;
}

.brief-content blockquote {
    border-left: 4px solid var(--accent-color);
    padding-left: 20px;
    margin: 20px 0;
    font-style: italic;
    opacity: 0.8;
}

.archive {
    margin-top: 40px;
    padding-top: 30px;
    border-top: 1px solid #eee;
}

.archive h2 {
    margin-bottom: 20px;
}

.archive ul {
    list-style: none;
}

.archive li {
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
}

.archive a {
    color: var(--text-color);
    text-decoration: none;
}

.archive a:hover {
    color: var(--accent-color);
}

footer {
    text-align: center;
    padding: 20px;
    opacity: 0.6;
    font-size: 0.9rem;
}
"""
        self._write_file("style.css", css_content)


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ subtitle }}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
    </header>

    <div class="container">
        <main>
            <article class="brief-content">
                {{ brief_content }}
            </article>

            <section class="archive">
                <h2>历史早报</h2>
                <ul>
                {% for brief in briefs %}
                    <li>
                        <a href="{{ brief.path }}">{{ brief.date }} - {{ brief.title }}</a>
                    </li>
                {% endfor %}
                </ul>
            </section>
        </main>

        <footer>
            <p>{{ title }} | 由 AI 自动生成</p>
        </footer>
    </div>
</body>
</html>
"""
