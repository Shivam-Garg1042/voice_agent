"""Voice pipeline construction.

Centralizes how the STT -> LLM -> TTS -> VAD -> turn-detection stack is wired
so the rest of the app never hard-codes model names or voice ids. `main.py`
just asks for a session; swapping a provider happens here (and via `.env`).
"""

from __future__ import annotations

import logging

from livekit.agents import AgentSession
from livekit.agents.vad import VAD
from livekit.plugins import cartesia, deepgram, google, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from services.config import AppConfig

logger = logging.getLogger(__name__)


def load_vad() -> VAD:
    """Load the Silero VAD. Call this once at prewarm, not per call."""
    return silero.VAD.load()


def build_session(config: AppConfig, vad: VAD) -> AgentSession:
    """Build a fully-configured AgentSession from app config + a prewarmed VAD.

    Turn detection uses the multilingual model (better for Hinglish back-and-forth)
    when enabled; otherwise it falls back to plain VAD endpointing.
    """
    turn_detection = MultilingualModel() if config.use_turn_detector else "vad"

    logger.info(
        "[Chargeup] Pipeline: stt=%s llm=%s tts=%s/%s turn_detector=%s",
        config.stt_model,
        config.llm_model,
        config.tts_model,
        config.tts_language,
        config.use_turn_detector,
    )

    return AgentSession(
        stt=deepgram.STT(model=config.stt_model, language="multi"),
        llm=google.LLM(model=config.llm_model),
        tts=cartesia.TTS(
            model=config.tts_model,
            voice=config.tts_voice,
            language=config.tts_language,
            speed=config.tts_speed,
        ),
        vad=vad,
        turn_detection=turn_detection,
    )
