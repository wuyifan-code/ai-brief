# AI 早报自动生产线

自动采集 RSS/GitHub AI 资讯，AI 去重、评分、聚类、生成文字早报，再生成 16:9 横屏视频，并发布到 GitHub 仓库。

## 功能特性

- **自动采集**: RSS feeds + GitHub Releases/Events
- **AI 处理**: 去重、评分、关键词提取、摘要生成
- **视频生成**: 1920x1080 横屏 + MiniMax TTS 语音 + SRT 字幕
- **多平台发布**: GitHub 仓库归档 + GitHub Pages 静态站点 + RSS Feed
- **可配置**: 支持自定义信息源、权重、评分阈值

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/wuyifan-code/ai-brief.git
cd ai-brief

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .

# 安装 playwright（用于截图）
playwright install chromium
```

### 2. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
# OpenAI API
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_FAST=gpt-4o-mini
OPENAI_MODEL_WRITER=gpt-4o

# MiniMax TTS
MINIMAX_API_KEY=your-minimax-key
MINIMAX_API_HOST=https://api.minimax.chat
EOF
```

### 3. 配置信息源

编辑 `config/sources.yaml`:

```yaml
rss:
  - url: "https://example.com/feed.xml"
    category: "AI"
    weight: 8
    enabled: true

github:
  repos:
    - owner: "openai"
      repo: "chatgpt"
      category: "LLM"
      weight: 10
      enabled: true
```

### 4. 运行

```bash
# 采集今日资讯
python -m ai_brief collect --date 2026-05-02

# 构建早报
python -m ai_brief build --date 2026-05-02

# 渲染视频（需要 ffmpeg）
python -m ai_brief render-video --date 2026-05-02

# 发布
python -m ai_brief publish --date 2026-05-02 --review-required

# 或一键运行完整流程
python -m ai_brief run-daily --date 2026-05-02
```

## 命令行接口

| 命令 | 说明 |
|------|------|
| `collect` | 采集 RSS/GitHub 资讯 |
| `build` | AI 处理 + 生成 Markdown 早报 |
| `render-video` | 渲染视频（截图 + TTS + 合成） |
| `publish` | 发布到 GitHub |
| `run-daily` | 完整流水线 |

## 项目结构

```
ai_brief/
├── config/
│   └── sources.yaml          # 信息源配置
├── src/ai_brief/
│   ├── cli.py                # 命令行入口
│   ├── config.py             # 配置加载
│   ├── collect/              # 采集模块
│   │   ├── rss.py
│   │   └── github.py
│   ├── build/                # 构建模块
│   │   ├── dedup.py
│   │   ├── rank.py
│   │   └── compose.py
│   ├── render/               # 渲染模块
│   │   ├── card.py
│   │   ├── screenshot.py
│   │   ├── tts.py
│   │   └── video.py
│   └── publish/              # 发布模块
│       ├── site.py
│       ├── rss.py
│       └── github.py
├── data/
│   ├── raw/                  # 原始采集数据
│   └── processed/            # AI 处理后数据
├── content/daily/            # 生成的早报
├── media/                    # 视频素材
├── site/                    # 静态站点
└── tests/                   # 测试
```

## 外部依赖

- **ffmpeg**: 视频合成（必须）
  - Windows: `winget install ffmpeg` 或从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

- **playwright**: 浏览器截图
  - `playwright install chromium`

- **gh CLI**: GitHub 发布（可选）
  - `winget install gh` 或从 [cli.github.com](https://cli.github.com/) 下载

## GitHub Actions 自动部署

推送代码后，在 GitHub 仓库设置中启用 GitHub Pages，选择 `gh-pages` 分支。

添加 Secrets:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL_FAST`
- `OPENAI_MODEL_WRITER`
- `MINIMAX_API_KEY`

## License

MIT
