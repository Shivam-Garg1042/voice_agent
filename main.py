"""
main.py
Chargeup Voice Agent Platform entry point.

Run locally:
    python main.py download-files   # one-time: fetch the turn-detector model
    python main.py dev

This process registers a LiveKit worker. When LiveKit assigns a room/job to the
worker, `entrypoint()` runs: it looks up the driver, picks the right agent
(Neha = collections, Khushi = sales), and starts the voice session.
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli

from agents.collections_agent import create_collections_agent
from agents.sales_agent import create_sales_agent
from services.config import load_app_config
from services.events import EventLogger
from services.mock_crm import load_driver_profile, serialize_driver_profile
from services.pipeline import build_session, load_vad

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def prewarm(proc: JobProcess) -> None:
    """Runs once per worker process, before any call.

    Loads the heavy Silero VAD a single time and validates config up front so a
    misconfigured worker fails at boot instead of mid-call.
    """
    config = load_app_config()
    proc.userdata["config"] = config
    proc.userdata["event_logger"] = EventLogger(config.events_log_path)
    proc.userdata["vad"] = load_vad()
    logger.info("[Chargeup] Prewarm complete. Event log: %s", config.events_log_path)


async def entrypoint(ctx: JobContext) -> None:
    """Called once per incoming call / session."""
    config = ctx.proc.userdata["config"]
    event_logger: EventLogger = ctx.proc.userdata["event_logger"]
    vad = ctx.proc.userdata["vad"]

    profile = load_driver_profile(room_name=ctx.room.name)
    driver_context = serialize_driver_profile(profile)

    logger.info(
        "[Chargeup] New call | Room: %s | Driver: %s | Agent: %s | Due: %s | Scenario: %s",
        ctx.room.name,
        profile.driver_name,
        profile.agent_type,
        profile.due_date,
        profile.scenario,
    )
    event_logger.write(
        "call_received",
        {"room_name": ctx.room.name, "driver": driver_context},
    )

    await ctx.connect()

    if profile.agent_type == "sales":
        agent = create_sales_agent(
            lead_name=profile.driver_name,
            call_type=profile.call_type,
            event_logger=event_logger,
            driver_context=driver_context,
        )
    else:
        agent = create_collections_agent(
            driver_name=profile.driver_name,
            due_date=profile.due_date,
            scenario=profile.scenario,
            event_logger=event_logger,
            driver_context=driver_context,
        )

    session = build_session(config, vad)

    logger.info("[Chargeup] Session starting for driver: %s", profile.driver_name)
    event_logger.write(
        "session_starting",
        {"room_name": ctx.room.name, "driver": driver_context},
    )

    await session.start(room=ctx.room, agent=agent)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
