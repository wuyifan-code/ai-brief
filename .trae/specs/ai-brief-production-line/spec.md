# AI 早报自动生产线规范

## Why
需要一套自动化系统，每日采集 AI/科技领域热点资讯，通过 AI 处理生成结构化早报，并自动生成视频内容发布到多平台。

## What Changes
- **信息采集**：RSS Feed + GitHub API，72小时时间窗口
- **内容构建**：URL/标题去重 → LLM 评分排序 → 事件聚类 → Markdown 生成
- **视频渲染**：1920x1080 HTML 卡片 → Playwright 截图 → MiniMax TTS 语音合成 → FFmpeg 视频合成
- **自动发布**：静态站点 + RSS Feed + GitHub Actions 定时部署

## Impact
- 影响项目结构：完整的 `src/ai_brief/` 模块化架构
- 影响依赖：`openai`, `minimax`, `feedparser`, `playwright`, `pyyaml`, `jinja2`
- 影响环境变量：`OPENAI_API_KEY`, `MINIMAX_API_KEY`, `GITHUB_TOKEN`

## ADDED Requirements

### Requirement: RSS 信息采集
系统 SHALL 支持从配置的多源 RSS Feed 采集新闻条目。

#### Scenario: 正常采集
- **WHEN** 执行 `python -m ai_brief run-daily --date 2026-05-02`
- **THEN** 系统从 `config/sources.yaml` 读取 RSS 源，过滤 72 小时内条目，返回标题/链接/摘要/发布时间

### Requirement: GitHub Trending 采集
系统 SHALL 支持通过 GitHub API 采集指定仓库的最近更新。

#### Scenario: GitHub 采集
- **WHEN** 配置中包含 GitHub 仓库列表
- **THEN** 系统通过 API 获取近期活跃的 issue/PR，返回标题/URL/星标数

### Requirement: 智能去重
系统 SHALL 支持 URL 精确去重和标题模糊去重。

#### Scenario: 去重处理
- **WHEN** 采集到重复 URL
- **THEN** 系统跳过该条目
- **AND WHEN** 标题相似度 > 0.85
- **THEN** 系统合并或丢弃低分条目

### Requirement: LLM 新闻评分
系统 SHALL 调用 OpenAI API 对新闻进行 relevance/speed/impact 三维度评分。

#### Scenario: 评分生成
- **WHEN** 待评分新闻条目存在
- **THEN** 系统生成 0-100 综合评分，并附带简短理由

### Requirement: 事件聚类
系统 SHALL 将相似新闻聚类为同一事件，生成统一摘要。

#### Scenario: 聚类处理
- **WHEN** 存在多篇相似新闻
- **THEN** 系统按时间线组织，生成事件标题和核心要点

### Requirement: Markdown 日报生成
系统 SHALL 生成符合模板的 Markdown 格式日报。

#### Scenario: 日报生成
- **WHEN** 内容构建完成
- **THEN** 系统输出包含时间锚点、分类标签、链接列表的 Markdown 文件

### Requirement: HTML 卡片渲染
系统 SHALL 将每条新闻渲染为 1920x1080 HTML 卡片。

#### Scenario: 卡片生成
- **WHEN** 需要生成视频帧
- **THEN** 系统使用 Jinja2 模板渲染 HTML，通过 Playwright 截图保存为 PNG

### Requirement: MiniMax TTS 语音合成
系统 SHALL 调用 MiniMax TTS API 生成中文语音旁白。

#### Scenario: 语音生成
- **WHEN** 需要为视频添加配音
- **THEN** 系统使用新闻摘要生成语音，支持语速/音调参数调节

### Requirement: FFmpeg 视频合成
系统 SHALL 使用 FFmpeg 将图片帧和音频合成为 MP4 视频。

#### Scenario: 视频合成
- **WHEN** 存在图片帧序列和音频文件
- **THEN** 系统执行 FFmpeg 命令行，按顺序合成视频流

### Requirement: 静态站点生成
系统 SHALL 生成可部署的 HTML 静态站点。

#### Scenario: 站点生成
- **WHEN** 日报生成完成后
- **THEN** 系统渲染首页和详情页，包含响应式布局和暗色主题

### Requirement: RSS Feed 生成
系统 SHALL 生成符合规范的 RSS XML 文件。

#### Scenario: RSS 生成
- **WHEN** 日报内容更新
- **THEN** 系统更新 `feed.xml`，包含完整 metadata 和 enclosure

### Requirement: GitHub 自动发布
系统 SHALL 支持自动检测 `gh` CLI、安装认证、创建/更新仓库。

#### Scenario: GitHub 发布
- **WHEN** 配置启用 GitHub 发布
- **THEN** 系统检测 `gh` 是否存在，不存在则提示安装命令；认证后自动创建仓库并推送

### Requirement: GitHub Actions 定时任务
系统 SHALL 配置每日定时执行的 GitHub Actions 工作流。

#### Scenario: CI/CD 触发
- **WHEN** 代码推送到 GitHub
- **THEN** Actions 自动运行 `run-daily` 命令，生成当日早报

## MODIFIED Requirements

### Requirement: CLI 入口
- **原始**：简单命令行参数解析
- **修改为**：基于 Click 的完整 CLI，支持 `run-daily`, `build-video`, `publish` 等子命令

## REMOVED Requirements

### Requirement: 旧版手动发布流程
**Reason**: 已由自动化 GitHub Actions 替代
**Migration**: 用户无需手动上传文件，CI/CD 自动完成

## Technical Constraints
- **FFmpeg**：必须在 PATH 中可访问，版本 >= 4.0
- **Playwright**：需要安装浏览器驱动 `playwright install chromium`
- **Python**：>= 3.9，异步 I/O 支持
- **API 限流**：LLM 调用添加退避重试，TTS 并发限制为 3

## Dependencies
```
openai>=1.0.0
minimax>=0.1.0
feedparser>=6.0.0
playwright>=1.40.0
pyyaml>=6.0
jinja2>=3.1.0
click>=8.0.0
aiohttp>=3.9.0
```