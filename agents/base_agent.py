"""
Base class for Chargeup voice agents.
Shared instructions and reusable tools live here.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from livekit.agents import Agent, RunContext, function_tool

from services.events import EventLogger

logger = logging.getLogger(__name__)


class ChargeupBaseAgent(Agent):
    """
    Base agent for all Chargeup voice calls.
    Provides shared instructions, tools, and call metadata.
    """

    BASE_INSTRUCTIONS = """
## Language & Voice Rules
- Speak conversational Hinglish, mostly in Hindi script with simple finance and app words in English.
- This is a phone call. Keep every response short, usually 2-3 sentences max.
- Never use bullet points, markdown, or emoji in spoken responses.
- Natural fillers are okay: "जी सर", "मैं समझ सकती हूँ", "ठीक है", "जी समझ गई".
- Never say you are an AI, bot, or that the call is recorded.
- Stay within payment, due dates, penalties, CIBIL impact, payment methods, and battery issues.

## Money Pronunciation
- ₹300 should be spoken as "तीन सौ रुपये".
- ₹1500 should be spoken as "पंद्रह सौ रुपये".
- Always say "तीन सौ रुपये की penalty", not just "penalty".

## Waiting Rule
- If the driver says "ek min ruk jao" or says they are driving, acknowledge and wait silently.
- Do not hang up while waiting.

## Voicemail Rule
- If an automated machine answers or there is a voicemail prompt, immediately call hangup() and do not speak.

## Inappropriate Language
- If the customer uses abusive language, say exactly:
  "माफ़ कीजिये Sir, पर मैं इस तरह की भाषा के साथ आगे बात नहीं कर पाऊँगी। मुझे अब ये call disconnect करनी होगी। धन्यवाद।"
- Then immediately call hangup().

## Call Closing
- Always end with: "Chargeup को अपना समय देने के लिए धन्यवाद। आपका दिन शुभ हो।"
- After the driver says "ठीक है", "okay", "bye", or any closing acknowledgment, call hangup().
- Do not speak after calling hangup().
"""

    def __init__(
        self,
        instructions: str,
        driver_name: str = "Sir",
        event_logger: Optional[EventLogger] = None,
        driver_context: Optional[dict] = None,
    ):
        full_instructions = self.BASE_INSTRUCTIONS + "\n\n" + instructions
        super().__init__(instructions=full_instructions)
        self.driver_name = driver_name
        self.event_logger = event_logger
        self.driver_context = driver_context or {}

    @function_tool
    async def hangup(self, context: RunContext):
        """End the call cleanly."""
        logger.info("[Chargeup] hangup() called - ending call for driver: %s", self.driver_name)
        self._write_event("call_hangup_requested", {})
        await context.session.aclose()
        return "Call ended."

    @function_tool
    async def transfer_to_human(self, context: RunContext, reason: str):
        """
        Escalate to a human agent for complex issues or repeated refusal.
        """
        logger.info(
            "[Chargeup] ESCALATION - Driver: %s | Reason: %s | Time: %s",
            self.driver_name,
            reason,
            datetime.now(),
        )
        self._write_event(
            "transfer_to_human",
            {
                "reason": reason,
            },
        )
        return f"Escalation logged: {reason}"

    @function_tool
    async def log_complaint(self, context: RunContext, complaint_type: str, details: str):
        """Log a complaint, hardship note, or follow-up reason."""
        logger.info(
            "[Chargeup] LOG - Driver: %s | Type: %s | Details: %s | Time: %s",
            self.driver_name,
            complaint_type,
            details,
            datetime.now(),
        )
        self._write_event(
            "complaint_logged",
            {
                "complaint_type": complaint_type,
                "details": details,
            },
        )
        return f"Complaint logged: {complaint_type}"

    def _write_event(self, event_type: str, payload: dict) -> None:
        if self.event_logger is None:
            return
        self.event_logger.write(
            event_type,
            {
                "driver_name": self.driver_name,
                "driver_context": self.driver_context,
                **payload,
            },
        )
