# AI 早报自动生产线 - 验证清单

## 阶段一：项目基础

- [x] pyproject.toml 包含所有必需依赖（openai, minimax, feedparser, playwright, pyyaml, jinja2, click, aiohttp）
- [x] pyproject.toml 定义正确的入口点 `ai_brief = ai_brief.cli:main`
- [x] config.example.yaml 包含完整的配置项说明
- [x] src/ai_brief/config.py 正确加载 YAML 配置
- [x] 配置加载支持环境变量覆盖（OPENAI_API_KEY, MINIMAX_API_KEY, GITHUB_TOKEN）

## 阶段二：信息采集

- [x] rss.py 支持解析多个 RSS Feed URL
- [x] rss.py 过滤 72 小时内发布的条目
- [x] rss.py 返回标准化字段（title, url, summary, published_at）
- [x] github.py 使用 GitHub API 获取仓库活跃度
- [x] github.py 处理 API 限流（429 响应自动退避）
- [x] test_collect.py 包含 RSS 和 GitHub 采集的单元测试

## 阶段三：内容构建

- [x] dedup.py 实现 URL 精确去重
- [x] dedup.py 实现标题相似度去重（阈值 0.85）
- [x] rank.py 调用 OpenAI API 生成新闻评分
- [x] rank.py 评分维度包含 relevance/speed/impact
- [x] cluster.py 按语义相似度聚类新闻事件
- [x] compose.py 生成符合模板的 Markdown 输出
- [x] test_build.py 包含构建模块的单元测试

## 阶段四：视频渲染

- [x] card.py 使用 Jinja2 模板渲染 1920x1080 HTML 卡片
- [x] card.py 支持深色主题样式
- [x] screenshot.py 使用 Playwright 无头浏览器截图
- [x] screenshot.py 输出 PNG 格式，1920x1080 分辨率
- [x] tts.py 正确调用 MiniMax TTS API
- [x] tts.py 支持中文语音生成
- [x] tts.py 实现并发限制（最多 3 个并行请求）
- [x] video.py 使用 FFmpeg 合成图片帧和音频
- [x] video.py 输出 MP4 格式，H.264 编码
- [x] test_render.py 包含渲染模块的单元测试

## 阶段五：发布系统

- [x] site.py 生成响应式 HTML 静态页面
- [x] site.py 包含当日早报完整内容
- [x] rss.py 生成符合规范的 RSS 2.0 XML
- [x] rss.py 包含正确的时间戳和 enclosure 标签
- [x] github.py 检测 `gh` CLI 是否安装
- [x] github.py 在未安装时提示安装命令
- [x] github.py 自动完成 GitHub 认证
- [x] github.py 自动创建仓库（如不存在）
- [x] .github/workflows/daily.yml 配置每日定时触发
- [x] daily.yml 正确配置环境变量和依赖安装

## 阶段六：CLI 与集成

- [x] cli.py 使用 Click 框架实现子命令
- [x] cli.py 支持 `run-daily` 命令（完整流程）
- [x] cli.py 支持 `build-video` 命令（仅生成视频）
- [x] cli.py 支持 `publish` 命令（仅发布）
- [x] cli.py 支持 `--date` 参数指定日期
- [x] config/sources.yaml 包含示例 RSS 源配置
- [x] README.md 包含快速开始指南
- [x] README.md 列出所有环境变量要求

## 端到端验证

- [x] 完整流程 `python -m ai_brief run-daily --date 2026-05-02` 可正常运行
- [x] 生成的 Markdown 日报格式正确
- [x] 生成的视频文件可播放（MP4，H.264）
- [x] GitHub Actions 工作流在定时触发时正常执行