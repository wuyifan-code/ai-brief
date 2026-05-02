"""视频合成模块"""

import subprocess
from pathlib import Path
from typing import Any


class VideoRenderer:
    """视频渲染器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.video_config = config.get("video", {})
        self.fps = self.video_config.get("fps", 30)

    def render(
        self,
        date: str,
        screenshots: list[Path],
        audio: Path | None,
        subtitle: Path,
        output_dir: Path,
    ) -> Path:
        """渲染最终视频"""
        output_path = output_dir / f"{date}.mp4"

        if not screenshots:
            print("[video] 没有截图素材，跳过视频渲染")
            return output_path

        # 检查 ffmpeg 是否可用
        if not self._check_ffmpeg():
            print("[video] 未检测到 ffmpeg，请安装: https://ffmpeg.org/download.html")
            print("[video] Windows: winget install ffmpeg 或从官网下载")
            return output_path

        try:
            # 方案1: 使用 ffmpeg concat 合成
            if audio and audio.exists():
                self._render_with_audio(screenshots, audio, subtitle, output_path)
            else:
                self._render_without_audio(screenshots, subtitle, output_path)

        except Exception as e:
            print(f"[video] 渲染失败: {e}")

        return output_path

    def _check_ffmpeg(self) -> bool:
        """检查 ffmpeg 是否可用"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _render_with_audio(
        self,
        screenshots: list[Path],
        audio: Path,
        subtitle: Path,
        output: Path,
    ) -> None:
        """有音频的渲染"""
        # 1. 创建文件列表
        concat_list = output.parent / "concat_list.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for screenshot in screenshots:
                f.write(f"file '{screenshot.absolute()}'\n")
                f.write(f"duration {self._estimate_duration(screenshot)}\n")

        # 2. 获取音频时长
        audio_duration = self._get_duration(audio)

        # 3. 合成视频
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-vf",
            f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            str(output),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # 清理临时文件
        concat_list.unlink(missing_ok=True)

    def _render_without_audio(
        self,
        screenshots: list[Path],
        subtitle: Path,
        output: Path,
    ) -> None:
        """无音频的渲染（字幕视频草稿）"""
        # 1. 创建文件列表
        concat_list = output.parent / "concat_list.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for screenshot in screenshots:
                f.write(f"file '{screenshot.absolute()}'\n")
                f.write(f"duration {self._estimate_duration(screenshot)}\n")

        # 2. 合成视频（无音频）
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-vf",
            f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-frames:v",
            str(len(screenshots) * 150),  # 每张图约5秒
            str(output),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # 清理临时文件
        concat_list.unlink(missing_ok=True)

    def _estimate_duration(self, screenshot: Path) -> float:
        """估算单张截图的显示时长"""
        # 默认 5 秒
        return 5.0

    def _get_duration(self, media_path: Path) -> float:
        """获取媒体文件时长"""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(media_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return 5.0


def generate_subtitle(brief_path: Path, audio_duration: float, output_path: Path) -> Path:
    """生成 SRT 字幕文件"""
    content = brief_path.read_text(encoding="utf-8")

    import re

    # 提取新闻标题和摘要
    pattern = r"### \d+\. (.+?)\n\n.+?\n\n(.+?)\n\n"
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        return output_path

    # 计算每段的时长
    total_items = len(matches)
    segment_duration = audio_duration / total_items if total_items > 0 else 5.0

    srt_content = ""
    for i, (title, summary) in enumerate(matches, 1):
        start_time = (i - 1) * segment_duration
        end_time = i * segment_duration

        start_srt = _format_srt_time(start_time)
        end_srt = _format_srt_time(end_time)

        text = f"{title}。{summary[:50]}"

        srt_content += f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n"

    output_path.write_text(srt_content, encoding="utf-8")
    return output_path


def _format_srt_time(seconds: float) -> str:
    """格式化 SRT 时间"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
