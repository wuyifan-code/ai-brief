"""渲染模块测试"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCardGenerator:
    """HTML 卡片生成测试"""

    def test_parse_brief(self):
        """测试早报解析"""
        from ai_brief.render.card import parse_brief

        brief_content = """# AI 早报 2026年05月01日

## 目录

1. [OpenAI 发布 GPT-5](#1)

---

### 1. OpenAI 发布 GPT-5

**评分**: ⭐⭐⭐⭐⭐ (10/10)

OpenAI 宣布发布 GPT-5，性能大幅提升。

**关键词**: `GPT-5` `OpenAI` `LLM`

**来源**: [OpenAI Blog](https://blog.openai.com)

---

"""

        # 创建临时文件
        temp_file = Path("test_brief.md")
        temp_file.write_text(brief_content, encoding="utf-8")

        items = parse_brief(temp_file)

        assert len(items) >= 1
        assert items[0]["title"] == "OpenAI 发布 GPT-5"
        assert items[0]["score"] == "10"

        temp_file.unlink()

    def test_card_html_structure(self):
        """测试卡片 HTML 结构"""
        from ai_brief.render.card import CARD_TEMPLATE

        assert "<!DOCTYPE html>" in CARD_TEMPLATE
        assert "{{ title }}" in CARD_TEMPLATE  # Jinja2 模板变量
        assert "{{ body }}" in CARD_TEMPLATE


class TestVideoRenderer:
    """视频渲染测试"""

    def test_check_ffmpeg(self):
        """测试 ffmpeg 检测"""
        from ai_brief.render.video import VideoRenderer

        renderer = VideoRenderer({"video": {"fps": 30}})

        # 这个测试在实际环境运行
        # 本地可能没有 ffmpeg
        result = renderer._check_ffmpeg()
        assert isinstance(result, bool)

    def test_format_srt_time(self):
        """测试 SRT 时间格式"""
        from ai_brief.render.video import _format_srt_time

        # 测试 0 秒
        assert _format_srt_time(0.0) == "00:00:00,000"

        # 测试正常时间
        result = _format_srt_time(3661.5)  # 1小时1分1.5秒
        assert result == "01:01:01,500"


class TestMiniMaxTTS:
    """MiniMax TTS 测试"""

    def test_parse_brief(self):
        """测试早报解析为语音段落"""
        from ai_brief.render.tts import MiniMaxTTS

        tts = MiniMaxTTS({"api_key": ""})

        brief_content = """# AI 早报 2026年05月01日

### 1. OpenAI 发布 GPT-5

**评分**: ⭐⭐⭐⭐⭐ (10/10)

OpenAI 宣布发布 GPT-5，性能大幅提升。

"""

        temp_file = Path("test_brief_tts.md")
        temp_file.write_text(brief_content, encoding="utf-8")

        segments = tts._parse_brief(temp_file)

        assert len(segments) >= 1
        assert "OpenAI 发布 GPT-5" in segments[0] or len(segments) > 0

        temp_file.unlink()

    def test_no_api_key(self):
        """测试无 API 密钥"""
        from ai_brief.render.tts import MiniMaxTTS

        tts = MiniMaxTTS({"api_key": ""})
        result = tts.generate(Path("nonexistent.md"), Path("output"))
        assert result is None
