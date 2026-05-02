# AI 早报自动生产线 - 实施计划

## Context

构建一个从零开始的全自动化 AI 早报生产线，实现：
- **采集层**：RSS/GitHub 资讯自动采集
- **AI 处理层**：去重、评分、聚类、生成 Markdown 早报
- **视频层**：16:9 横屏视频生成（TTS + 字幕 + 画面合成）
- **发布层**：GitHub 仓库归档 + GitHub Pages 静态站点 + RSS Feed

第一版追求"尽量全自动"，保留 `--review-required` 人工审核开关。

---

## 项目架构

```
ai_brief/
├── config/
│   └── sources.yaml          # 信息源配置
├── src/ai_brief/
│   ├── __init__.py
│   ├── cli.py                # 命令行入口
│   ├── collect/
│   │   ├── __init__.py
│   │   ├── rss.py             # RSS 采集器
│   │   └── github.py          # GitHub 采集器
│   ├── build/
│   │   ├── __init__.py
│   │   ├── dedup.py           # 去重引擎
│   │   ├── rank.py            # 新闻评分
│   │   ├── cluster.py         # 事件聚类
│   │   └── compose.py         # Markdown 生成
│   ├── render/
│   │   ├── __init__.py
│   │   ├── card.py            # HTML 卡片生成
│   │   ├── screenshot.py      # 浏览器截图
│   │   ├── tts.py             # TTS provider 抽象
│   │   └── video.py           # ffmpeg 视频合成
│   └── publish/
│       ├── __init__.py
│       ├── site.py            # 静态站点生成
│       ├── rss.py             # RSS Feed 生成
│       └── github.py          # GitHub API 发布
├── data/
│   ├── raw/                   # 原始采集数据 .jsonl
│   ├── processed/            # AI 处理后数据 .json
│   └── daily/                 # 最终 Markdown 早报
├── media/                     # 视频素材、字幕、成品
├── site/                      # GitHub Pages 静态站点
├── tests/
│   ├── test_collect.py
│   ├── test_build.py
│   └── test_render.py
├── pyproject.toml
├── config.example.yaml
└── README.md
```

---

## 实施步骤

### Phase 1：项目脚手架（1-2 小时）

1. **创建 `pyproject.toml`**
   - 依赖：httpx, feedparser, PyYAML, jinja2, playwright, openai
   - Python 3.11+

2. **创建 `config/sources.yaml` 配置结构**
   - RSS feeds 列表（分类、权重、启用状态）
   - GitHub 关注仓库列表（组织、仓库名、关键词）
   - Publishing 配置（站点标题、作者）
   - Video 配置（尺寸 1920x1080、字体、主题色）

3. **创建 CLI 入口 `src/ai_brief/cli.py`**
   - `collect --date` / `build --date` / `render-video --date` / `publish --date` / `run-daily --date`
   - `--review-required` 标志

### Phase 2：采集层（2-3 小时）

4. **RSS 采集器 `collect/rss.py`**
   - 使用 `feedparser` 解析 RSS/Atom
   - 提取：title, link, published, summary, source
   - 写入 `data/raw/{date}.jsonl`

5. **GitHub 采集器 `collect/github.py`**
   - GitHub REST API v3（避免认证复杂性）
   - 采集：Releases、Repository events
   - 写入 `data/raw/{date}.jsonl`

### Phase 3：AI 处理层（4-6 小时）

6. **去重引擎 `build/dedup.py`**
   - URL 完全匹配去重
   - 标题相似度去重（编辑距离或 embedding）
   - 72 小时历史窗口去重

7. **新闻评分 `build/rank.py`**
   - 调用 LLM 打分（1-10）
   - 低于阈值（默认 5 分）过滤

8. **事件聚类 `build/cluster.py`**
   - 关键词提取
   - 相似事件合并

9. **文章生成 `build/compose.py`**
   - 调用 LLM 生成：
     - 50 字摘要
     - 关键词
     - Markdown 正文（含目录、来源链接）
   - 输出 `content/daily/{date}.md`

### Phase 4：视频层（3-4 小时）

10. **HTML 卡片生成 `render/card.py`**
    - Jinja2 模板生成 1920x1080 HTML 页面
    - 每条新闻一张卡片

11. **浏览器截图 `render/screenshot.py`**
    - Playwright 截图生成图片素材

12. **TTS 抽象 `render/tts.py`**
    - HTTP TTS provider 抽象
    - 第一版支持任意 HTTP TTS API
    - 未配置时输出字幕视频草稿（无音频）

13. **字幕生成 `render/subtitle.py`**
    - 生成 SRT 字幕文件

14. **视频合成 `render/video.py`**
    - ffmpeg 合成最终 MP4
    - 需要用户安装 ffmpeg（项目中加入安装说明）

### Phase 5：发布层（2-3 小时）

15. **静态站点 `publish/site.py`**
    - 生成 HTML 索引页
    - 复制 Markdown 早报到 `site/daily/`

16. **RSS Feed `publish/rss.py`**
    - 生成 valid RSS 2.0 XML
    - 输出 `site/feed.xml`

17. **GitHub 发布 `publish/github.py`**
    - 创建新仓库（检测/提示安装 `gh` CLI）
    - GitHub Actions 定时任务（每天 8:00 Asia/Shanghai）
    - GitHub Pages 部署
    - `.github/workflows/daily-brief.yml`

### Phase 6：测试与文档（2-3 小时）

18. **单元测试**
    - RSS 解析（正常/空/重复/缺失日期）
    - GitHub 解析（release/event/重复）
    - 去重（URL/标题/72小时窗口）
    - 评分过滤
    - Markdown 生成完整性

19. **集成测试**
    - Fixture 数据完整跑通 collect -> build
    - 无 API Key 错误处理
    - 无 TTS 时降级处理

20. **文档**
    - README.md
    - config.example.yaml
    - 部署说明（ffmpeg 安装、GitHub 设置）

---

## 关键依赖

| 依赖 | 用途 |
|------|------|
| `httpx` | HTTP 客户端 |
| `feedparser` | RSS 解析 |
| `PyYAML` | 配置文件 |
| `jinja2` | HTML 模板 |
| `playwright` | 浏览器截图 |
| `openai` | OpenAI compatible API |
| `minimax` | MiniMax TTS API（语音合成） |
| `gh` | GitHub CLI（自动创建仓库） |
| `ffmpeg` | 视频合成（用户安装） |

---

## MiniMax TTS 集成

```bash
# 环境变量
MINIMAX_API_KEY=...
MINIMAX_API_HOST=https://api.minimax.chat
MINIMAX_TTS_MODEL=speech-02-hd
```

- TTS Provider 路径：`src/ai_brief/render/tts.py`
- 使用 MiniMax TTS API 生成中文语音旁白
- 语音文件转为 MP3 用于视频合成

---

## GitHub 自动创建

1. **检测 `gh` CLI**：如果未安装，提示用户安装
2. **自动创建仓库**：
   - `gh repo create ai-brief --public --clone`
   - 初始化 .gitignore、LICENSE
3. **GitHub Actions**：
   - 定时触发（每天 8:00 Asia/Shanghai）
   - 支持手动触发
   - `workflow_dispatch` + `schedule`

---

## 环境变量

```bash
# OpenAI Compatible API
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
OPENAI_MODEL_FAST=gpt-4o-mini
OPENAI_MODEL_WRITER=gpt-4o

# MiniMax TTS
MINIMAX_API_KEY=...
MINIMAX_API_HOST=https://api.minimax.chat
MINIMAX_TTS_MODEL=speech-02-hd
```

---

## 验证方案

1. **本地手动验证**
   ```bash
   # 采集今日数据
   python -m ai_brief collect --date 2026-05-02

   # 构建早报
   python -m ai_brief build --date 2026-05-02

   # 渲染视频（需 ffmpeg）
   python -m ai_brief render-video --date 2026-05-02

   # 发布（需 GitHub 配置）
   python -m ai_brief publish --date 2026-05-02 --review-required
   ```

2. **GitHub Actions dry run**
   - 验证 CI 流程语法

3. **浏览器检查**
   - HTML 卡片 1920x1080 不溢出
   - 静态站点可访问

4. **RSS 验证**
   - feed.xml 可被新闻阅读器订阅

---

## 优先实现顺序

1. 项目脚手架 + 配置
2. RSS 采集（最快见效）
3. AI 处理流程（核心价值）
4. GitHub 发布流程
5. 视频生成（最后完成）
