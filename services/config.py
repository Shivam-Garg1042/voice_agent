"""Environment configuration helpers.

Single source of truth for everything the worker reads from the environment:
the required provider credentials *and* the tunable voice-pipeline settings.
Non-engineers can change the voice, model, or speed from `.env` without
touching Python.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


REQUIRED_ENV_VARS = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "DEEPGRAM_API_KEY",
    "GOOGLE_API_KEY",
    "CARTESIA_API_KEY",
)

PLACEHOLDER_VALUES = {
    "",
    "your-project.livekit.cloud",
    "your_livekit_api_key",
    "your_livekit_api_secret",
    "your_deepgram_api_key",
    "your_google_api_key",
    "your_cartesia_api_key",
    "wss://your-project.livekit.cloud",
}

# Pipeline defaults. Override any of these in `.env` (see .env.example).
DEFAULT_STT_MODEL = "nova-3"
DEFAULT_LLM_MODEL = "gemini-2.5-flash"
DEFAULT_TTS_MODEL = "sonic-3"
DEFAULT_TTS_VOICE = "f786b574-daa5-4673-aa0c-cbe3e8534c02"
DEFAULT_TTS_LANGUAGE = "hi"
DEFAULT_TTS_SPEED = 1.0


@dataclass(frozen=True)
class AppConfig:
    # Credentials
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    google_api_key: str
    cartesia_api_key: str

    # Local-dev / runtime
    events_log_path: str = "runtime/call_events.jsonl"

    # Voice pipeline (tunable via env)
    stt_model: str = DEFAULT_STT_MODEL
    llm_model: str = DEFAULT_LLM_MODEL
    tts_model: str = DEFAULT_TTS_MODEL
    tts_voice: str = DEFAULT_TTS_VOICE
    tts_language: str = DEFAULT_TTS_LANGUAGE
    tts_speed: float = DEFAULT_TTS_SPEED
    use_turn_detector: bool = True


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip() in PLACEHOLDER_VALUES


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def validate_required_env() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if _is_placeholder(os.getenv(name))]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables: "
            f"{joined}. Copy .env.example to .env and set real values before starting the worker."
        )


def load_app_config() -> AppConfig:
    validate_required_env()
    return AppConfig(
        livekit_url=os.environ["LIVEKIT_URL"],
        livekit_api_key=os.environ["LIVEKIT_API_KEY"],
        livekit_api_secret=os.environ["LIVEKIT_API_SECRET"],
        deepgram_api_key=os.environ["DEEPGRAM_API_KEY"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
        cartesia_api_key=os.environ["CARTESIA_API_KEY"],
        events_log_path=os.getenv("EVENTS_LOG_PATH", "runtime/call_events.jsonl"),
        stt_model=os.getenv("STT_MODEL", DEFAULT_STT_MODEL),
        llm_model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        tts_model=os.getenv("TTS_MODEL", DEFAULT_TTS_MODEL),
        tts_voice=os.getenv("TTS_VOICE", DEFAULT_TTS_VOICE),
        tts_language=os.getenv("TTS_LANGUAGE", DEFAULT_TTS_LANGUAGE),
        tts_speed=float(os.getenv("TTS_SPEED", str(DEFAULT_TTS_SPEED))),
        use_turn_detector=_env_bool("USE_TURN_DETECTOR", True),
    )
