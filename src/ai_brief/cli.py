"""AI 早报命令行入口"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ai_brief import __version__
from ai_brief.collect.github import GitHubCollector
from ai_brief.collect.rss import RSSCollector
from ai_brief.build.compose import BriefComposer
from ai_brief.build.dedup import DedupEngine
from ai_brief.build.rank import NewsRanker
from ai_brief.config import load_config, get_openai_config, get_minimax_config
from ai_brief.publish.github import GitHubPublisher
from ai_brief.publish.rss import RSSGenerator
from ai_brief.publish.site import SiteGenerator
from ai_brief.render.tts import MiniMaxTTS
from ai_brief.render.video import VideoRenderer
from ai_brief.render.screenshot import screenshot_cards
from ai_brief.render.card import generate_cards


def date_arg(value: str) -> str:
    """解析日期参数"""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效日期格式: {value}，期望 YYYY-MM-DD")


def setup_parser() -> argparse.ArgumentParser:
    """设置命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="ai-brief",
        description="AI 早报自动生产线",
    )
    parser.add_argument("--version", action="version", version=f"ai-brief {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # collect 命令
    collect_parser = subparsers.add_parser("collect", help="采集今日资讯")
    collect_parser.add_argument(
        "--date",
        type=date_arg,
        default=(datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d"),
        help="采集日期 (YYYY-MM-DD)",
    )

    # build 命令
    build_parser = subparsers.add_parser("build", help="构建早报")
    build_parser.add_argument("--date", type=date_arg, required=True, help="早报日期")
    build_parser.add_argument(
        "--review-required",
        action="store_true",
        help="发布前需要人工审核",
    )

    # render-video 命令
    render_parser = subparsers.add_parser("render-video", help="渲染视频")
    render_parser.add_argument("--date", type=date_arg, required=True, help="早报日期")

    # publish 命令
    publish_parser = subparsers.add_parser("publish", help="发布早报")
    publish_parser.add_argument("--date", type=date_arg, required=True, help="早报日期")
    publish_parser.add_argument(
        "--review-required",
        action="store_true",
        help="发布前需要人工审核",
    )

    # run-daily 命令
    daily_parser = subparsers.add_parser("run-daily", help="每日完整流程")
    daily_parser.add_argument(
        "--date",
        type=date_arg,
        default=(datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d"),
        help="运行日期",
    )
    daily_parser.add_argument(
        "--review-required",
        action="store_true",
        help="发布前需要人工审核",
    )

    return parser


def cmd_collect(date: str, config: dict) -> None:
    """执行采集命令"""
    print(f"[collect] 开始采集 {date} 的资讯...")

    # RSS 采集
    rss_collector = RSSCollector(config)
    rss_items = rss_collector.collect(date)
    print(f"[collect] RSS 采集完成: {len(rss_items)} 条")

    # GitHub 采集
    github_collector = GitHubCollector(config)
    github_items = github_collector.collect(date)
    print(f"[collect] GitHub 采集完成: {len(github_items)} 条")

    total = len(rss_items) + len(github_items)
    print(f"[collect] 共采集 {total} 条资讯")


def cmd_build(date: str, config: dict, review_required: bool) -> None:
    """执行构建命令"""
    print(f"[build] 开始构建 {date} 的早报...")

    openai_config = get_openai_config()
    raw_path = Path(f"data/raw/{date}.jsonl")

    if not raw_path.exists():
        print(f"[build] 错误: 找不到原始数据文件 {raw_path}")
        print(f"[build] 请先运行: python -m ai_brief collect --date {date}")
        sys.exit(1)

    # 去重
    dedup = DedupEngine(config, raw_path)
    deduped_items = dedup.run()
    print(f"[build] 去重完成: {len(deduped_items)} 条")

    # 评分
    ranker = NewsRanker(openai_config, config)
    scored_items = ranker.rank(deduped_items)
    print(f"[build] 评分完成: {len(scored_items)} 条")

    # 生成正文
    composer = BriefComposer(openai_config, config)
    brief = composer.compose(scored_items, date)

    output_path = Path(f"content/daily/{date}.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(brief, encoding="utf-8")
    print(f"[build] 早报已生成: {output_path}")

    if review_required:
        print(f"[build] 需要人工审核，文件已保存到: {output_path}")
        print(f"[build] 审核后请运行: python -m ai_brief publish --date {date}")


def cmd_render_video(date: str, config: dict) -> None:
    """执行渲染视频命令"""
    print(f"[render-video] 开始渲染 {date} 的视频...")

    brief_path = Path(f"content/daily/{date}.md")
    if not brief_path.exists():
        print(f"[render-video] 错误: 找不到早报文件 {brief_path}")
        sys.exit(1)

    media_dir = Path(f"media/{date}")
    media_dir.mkdir(parents=True, exist_ok=True)

    # 生成 HTML 卡片
    cards = generate_cards(brief_path, config)
    print(f"[render-video] 生成 {len(cards)} 张 HTML 卡片")

    # 截图
    screenshots = screenshot_cards(cards, media_dir)
    print(f"[render-video] 截图完成: {len(screenshots)} 张")

    # TTS 语音
    minimax_config = get_minimax_config()
    tts = MiniMaxTTS(minimax_config)
    audio_path = tts.generate(brief_path, media_dir)
    print(f"[render-video] TTS 生成完成: {audio_path}")

    # 生成字幕
    subtitle_path = media_dir / f"{date}.srt"
    print(f"[render-video] 字幕生成: {subtitle_path}")

    # 视频合成
    renderer = VideoRenderer(config)
    video_path = renderer.render(
        date=date,
        screenshots=screenshots,
        audio=audio_path,
        subtitle=subtitle_path,
        output_dir=media_dir,
    )
    print(f"[render-video] 视频渲染完成: {video_path}")


def cmd_publish(date: str, config: dict, review_required: bool) -> None:
    """执行发布命令"""
    print(f"[publish] 开始发布 {date} 的早报...")

    brief_path = Path(f"content/daily/{date}.md")
    if not brief_path.exists():
        print(f"[publish] 错误: 找不到早报文件 {brief_path}")
        sys.exit(1)

    if review_required:
        response = input("确认发布? (y/N): ")
        if response.lower() != "y":
            print("[publish] 已取消发布")
            return

    # 生成静态站点
    site_gen = SiteGenerator(config)
    site_gen.generate(date, brief_path)
    print("[publish] 静态站点已生成")

    # 生成 RSS
    rss_gen = RSSGenerator(config)
    rss_path = rss_gen.generate(date, brief_path)
    print(f"[publish] RSS Feed 已生成: {rss_path}")

    # 发布到 GitHub
    publisher = GitHubPublisher(config)
    publisher.publish(date)
    print("[publish] GitHub 发布完成")


def cmd_run_daily(date: str, config: dict, review_required: bool) -> None:
    """执行每日完整流程"""
    print(f"[run-daily] 开始每日流程: {date}")
    print("=" * 50)

    cmd_collect(date, config)
    print()

    cmd_build(date, config, review_required=True)
    print()

    video_response = input("是否渲染视频? (y/N): ")
    if video_response.lower() == "y":
        cmd_render_video(date, config)
        print()

    if review_required:
        response = input("是否发布? (y/N): ")
        if response.lower() == "y":
            cmd_publish(date, config, review_required=False)
    else:
        cmd_publish(date, config, review_required=False)

    print("=" * 50)
    print(f"[run-daily] 每日流程完成: {date}")


def main() -> None:
    """主入口"""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        config = load_config()

        if args.command == "collect":
            cmd_collect(args.date, config)
        elif args.command == "build":
            cmd_build(args.date, config, args.review_required)
        elif args.command == "render-video":
            cmd_render_video(args.date, config)
        elif args.command == "publish":
            cmd_publish(args.date, config, args.review_required)
        elif args.command == "run-daily":
            cmd_run_daily(args.date, config, args.review_required)

    except ValueError as e:
        print(f"配置错误: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        raise


if __name__ == "__main__":
    main()
