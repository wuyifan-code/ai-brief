"""配置加载模块"""

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = os.environ.get(
            "AI_BRIEF_CONFIG",
            Path(__file__).parent.parent.parent / "config" / "sources.yaml"
        )

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_env_or_raise(key: str, description: str) -> str:
    """获取环境变量，不存在则抛出异常"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"缺少环境变量 {key}: {description}")
    return value


def get_openai_config() -> dict[str, str]:
    """获取 OpenAI/MiniMax LLM API 配置"""
    # 支持 OpenAI 和 MiniMax（OpenAI 兼容 API）
    return {
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.minimaxi.com/v1"),
        "api_key": os.environ.get("OPENAI_API_KEY") or os.environ.get("MINIMAX_API_KEY", ""),
        "model_fast": os.environ.get("OPENAI_MODEL_FAST", "MiniMax-M2.7"),
        "model_writer": os.environ.get("OPENAI_MODEL_WRITER", "MiniMax-M2.7"),
    }


def get_minimax_config() -> dict[str, str]:
    """获取 MiniMax TTS 配置"""
    return {
        "api_key": get_env_or_raise("MINIMAX_API_KEY", "MiniMax API 密钥"),
        "api_host": os.environ.get("MINIMAX_API_HOST", "https://api.minimax.chat"),
        "tts_model": os.environ.get("MINIMAX_TTS_MODEL", "speech-02-hd"),
    }
