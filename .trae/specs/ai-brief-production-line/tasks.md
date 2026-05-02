# AI 早报自动生产线 - 实施任务

## 阶段一：项目基础

- [x] Task 1.1: 更新 `pyproject.toml`，添加所有依赖声明
- [x] Task 1.2: 创建 `config.example.yaml` 完整配置模板
- [x] Task 1.3: 实现 `src/ai_brief/config.py` 配置加载模块

## 阶段二：信息采集

- [x] Task 2.1: 实现 `src/ai_brief/collect/rss.py` RSS Feed 采集器
- [x] Task 2.2: 实现 `src/ai_brief/collect/github.py` GitHub API 采集器
- [x] Task 2.3: 编写 `tests/test_collect.py` 采集模块单元测试

## 阶段三：内容构建

- [x] Task 3.1: 实现 `src/ai_brief/build/dedup.py` URL/标题去重引擎
- [x] Task 3.2: 实现 `src/ai_brief/build/rank.py` LLM 新闻评分模块
- [x] Task 3.3: 实现 `src/ai_brief/build/cluster.py` 事件聚类算法
- [x] Task 3.4: 实现 `src/ai_brief/build/compose.py` Markdown 生成器
- [x] Task 3.5: 编写 `tests/test_build.py` 构建模块单元测试

## 阶段四：视频渲染

- [x] Task 4.1: 实现 `src/ai_brief/render/card.py` Jinja2 HTML 卡片模板
- [x] Task 4.2: 实现 `src/ai_brief/render/screenshot.py` Playwright 截图模块
- [x] Task 4.3: 实现 `src/ai_brief/render/tts.py` MiniMax TTS 语音合成
- [x] Task 4.4: 实现 `src/ai_brief/render/video.py` FFmpeg 视频合成
- [x] Task 4.5: 编写 `tests/test_render.py` 渲染模块单元测试

## 阶段五：发布系统

- [x] Task 5.1: 实现 `src/ai_brief/publish/site.py` 静态站点生成
- [x] Task 5.2: 实现 `src/ai_brief/publish/rss.py` RSS Feed 生成
- [x] Task 5.3: 实现 `src/ai_brief/publish/github.py` GitHub 自动发布（含 `gh` CLI 检测）
- [x] Task 5.4: 创建 `.github/workflows/daily.yml` GitHub Actions 工作流

## 阶段六：CLI 与集成

- [x] Task 6.1: 实现 `src/ai_brief/cli.py` Click 命令行入口
- [x] Task 6.2: 创建示例 `config/sources.yaml` 配置
- [x] Task 6.3: 更新 `README.md` 快速启动文档

## Task Dependencies
- [Task 1.2] 依赖 [Task 1.1]（配置模板需要依赖声明）
- [Task 1.3] 依赖 [Task 1.2]（需要示例配置）
- [Task 3.1-3.4] 依赖 [Task 2.1-2.2]（需要采集数据）
- [Task 4.1-4.4] 依赖 [Task 3.4]（需要生成内容）
- [Task 5.1-5.3] 依赖 [Task 4.4]（需要视频输出）
- [Task 6.1] 依赖 [Task 1.3, 2.1-2.2, 3.1-3.4, 4.1-4.4, 5.1-5.3]
- [Task 6.2-6.3] 依赖 [Task 6.1]