"""Mock CRM lookup for local development."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DriverProfile:
    driver_id: str
    phone_number: str
    driver_name: str
    agent_type: str
    call_type: str
    due_date: str
    scenario: str
    loan_amount: int
    battery_id: str


DEFAULT_DRIVER = DriverProfile(
    driver_id="DRV-001",
    phone_number="+919999999999",
    driver_name="Ramesh",
    agent_type="collections",
    call_type="",
    due_date="25 October",
    scenario="A",
    loan_amount=4200,
    battery_id="BAT-1001",
)


def load_driver_profile(room_name: str | None = None) -> DriverProfile:
    fixtures_path = os.getenv("MOCK_CRM_PATH", "mock_data/drivers.json")
    fixture_profile = _load_from_fixture(fixtures_path, room_name)
    if fixture_profile is not None:
        return fixture_profile

    return DriverProfile(
        driver_id=os.getenv("TEST_DRIVER_ID", DEFAULT_DRIVER.driver_id),
        phone_number=os.getenv("TEST_PHONE_NUMBER", DEFAULT_DRIVER.phone_number),
        driver_name=os.getenv("TEST_DRIVER_NAME", DEFAULT_DRIVER.driver_name),
        agent_type=os.getenv("TEST_AGENT_TYPE", DEFAULT_DRIVER.agent_type).lower(),
        call_type=os.getenv("TEST_CALL_TYPE", DEFAULT_DRIVER.call_type).upper(),
        due_date=os.getenv("TEST_DUE_DATE", DEFAULT_DRIVER.due_date),
        scenario=os.getenv("TEST_SCENARIO", DEFAULT_DRIVER.scenario).upper(),
        loan_amount=int(os.getenv("TEST_LOAN_AMOUNT", str(DEFAULT_DRIVER.loan_amount))),
        battery_id=os.getenv("TEST_BATTERY_ID", DEFAULT_DRIVER.battery_id),
    )


def serialize_driver_profile(profile: DriverProfile) -> dict:
    return asdict(profile)


def _load_from_fixture(path_str: str, room_name: str | None) -> DriverProfile | None:
    path = Path(path_str)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        records = json.load(handle)

    if not isinstance(records, list):
        return None

    if room_name:
        for record in records:
            if record.get("room_name") == room_name or record.get("phone_number") == room_name:
                return _profile_from_record(record)

    if records:
        return _profile_from_record(records[0])

    return None


def _profile_from_record(record: dict) -> DriverProfile:
    return DriverProfile(
        driver_id=record.get("driver_id", DEFAULT_DRIVER.driver_id),
        phone_number=record.get("phone_number", DEFAULT_DRIVER.phone_number),
        driver_name=record.get("driver_name", DEFAULT_DRIVER.driver_name),
        agent_type=record.get("agent_type", DEFAULT_DRIVER.agent_type).lower(),
        call_type=record.get("call_type", DEFAULT_DRIVER.call_type).upper(),
        due_date=record.get("due_date", DEFAULT_DRIVER.due_date),
        scenario=record.get("scenario", DEFAULT_DRIVER.scenario).upper(),
        loan_amount=int(record.get("loan_amount", DEFAULT_DRIVER.loan_amount)),
        battery_id=record.get("battery_id", DEFAULT_DRIVER.battery_id),
    )
