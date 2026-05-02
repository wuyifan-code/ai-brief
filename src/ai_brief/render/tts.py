"""MiniMax TTS 模块"""

import json
import time
from pathlib import Path
from typing import Any

import httpx


class MiniMaxTTS:
    """MiniMax TTS 语音合成"""

    def __init__(self, config: dict[str, str]):
        self.api_key = config.get("api_key", "")
        self.api_host = config.get("api_host", "https://api.minimax.chat")
        self.tts_model = config.get("tts_model", "speech-02-hd")

    def generate(self, brief_path: Path, output_dir: Path) -> Path | None:
        """生成语音文件"""
        if not self.api_key:
            print("[TTS] 未配置 MiniMax API 密钥，跳过语音生成")
            return None

        # 解析早报内容
        content = self._parse_brief(brief_path)
        if not content:
            print("[TTS] 无法解析早报内容")
            return None

        # 生成分段语音
        audio_path = output_dir / "audio.mp3"
        all_audio_data = []

        try:
            for i, segment in enumerate(content):
                print(f"[TTS] 生成第 {i + 1} 段语音...")
                audio_data = self._tts(segment)
                if audio_data:
                    all_audio_data.append(audio_data)
                time.sleep(0.5)  # 避免请求过快

            # 合并音频
            if all_audio_data:
                with audio_path.open("wb") as f:
                    for audio_data in all_audio_data:
                        f.write(audio_data)
                print(f"[TTS] 语音文件已生成: {audio_path}")
                return audio_path

        except Exception as e:
            print(f"[TTS] 生成失败: {e}")

        return None

    def _tts(self, text: str, voice_id: str = "male-qn-qingse") -> bytes | None:
        """调用 MiniMax TTS API"""
        url = f"{self.api_host}/v1/t2a_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.tts_model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "volume": 1.0,
                "pitch": 0,
            },
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                if data.get("data") and data["data"].get("audio_file"):
                    # 下载音频文件
                    audio_url = data["data"]["audio_file"]
                    audio_response = client.get(audio_url)
                    audio_response.raise_for_status()
                    return audio_response.content

        except Exception as e:
            print(f"[TTS] API 调用失败: {e}")

        return None

    def _parse_brief(self, brief_path: Path) -> list[str]:
        """解析早报为语音段落"""
        if not brief_path.exists():
            return []

        content = brief_path.read_text(encoding="utf-8")
        segments = []

        # 提取标题
        import re

        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        if title_match:
            segments.append(title_match.group(1))

        # 提取新闻标题和摘要
        pattern = r"### \d+\. (.+?)\n\n.+?\n\n(.+?)\n\n"
        matches = re.findall(pattern, content, re.DOTALL)

        for title, summary in matches:
            # 组合为语音文本
            segment = f"{title}。{summary}"
            segments.append(segment)

        # 添加结束语
        date_match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", content)
        if date_match:
            segments.append(f"以上就是 {date_match.group(1)} 的 AI 早报，感谢收听。")

        return segments
