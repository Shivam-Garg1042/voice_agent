# Engineering Handoff — Chargeup Voice Agent

_Last updated: 2026-06-16_

A one-page orientation for anyone picking up this project. Read the
[README](../README.md) first for setup; this doc covers **how it's built, what's
real, and what's left**.

---

## 1. What this is

An outbound voice-agent platform for Chargeup's EV battery finance business. It
makes automated calls (in Hinglish) to e-rickshaw drivers in India. Two
personas run on the same pipeline:

- **Neha** — collections / payment reminders.
- **Khushi** — sales / lead qualification.

It is a **LiveKit Agents worker**: a long-running process that registers with
LiveKit Cloud and is handed a "job" (a room) per call.

---

## 2. Architecture at a glance

```
LiveKit Cloud ──assigns a room/job──▶  Worker process (main.py)
                                         │
                            prewarm()  ──┤  load config + Silero VAD once
                                         │
                          entrypoint() ──┤  per call:
                                         │   1. mock_crm → DriverProfile
                                         │   2. pick agent (collections/sales)
                                         │   3. pipeline.build_session()
                                         │   4. session.start()
                                         ▼
                    STT (Deepgram) → LLM (Gemini) → TTS (Cartesia)
                    + Silero VAD + multilingual turn detector
```

**Key files & responsibilities**

| File | Responsibility |
|------|----------------|
| `main.py` | Worker lifecycle: `prewarm` (heavy load once) + `entrypoint` (per call). |
| `services/config.py` | The only place env vars are read. Validates creds, exposes tunable pipeline settings. |
| `services/pipeline.py` | The only place models/voices are wired. `build_session()`. |
| `services/mock_crm.py` | Stand-in for a CRM: room name → `DriverProfile`. |
| `services/events.py` | Append-only JSON-Lines audit log of call events. |
| `agents/base_agent.py` | `ChargeupBaseAgent`: shared Hinglish/voice rules + shared tools. |
| `agents/collections_agent.py` | Neha. Scenario A/B/C templates, objection bank, payment tools. |
| `agents/sales_agent.py` | Khushi. Locked product facts + pricing, lead handling. |
| `tools/payment.py` | Razorpay/CRM payment stubs (still simulated). |

**Design principles to preserve**
- **Hinglish-first.** Prompts are mostly Devanagari with English finance/app terms. Money is spelled phonetically in the prompt (e.g. `तीन सौ रुपये`) for correct TTS.
- **Config, not code.** Models, voice, and speed come from `.env`. Don't hard-code them back into Python.
- **Scenario templating.** Collections instructions are string templates with `{driver_name}` / `{due_date}` filled by the factory.
- **Everything notable is logged** to `runtime/call_events.jsonl`.

---

## 3. Agent tools (LLM-callable)

| Tool | Agent | Effect today |
|------|-------|--------------|
| `hangup()` | all | Ends the session. |
| `transfer_to_human(reason)` | all | Logs an escalation event. (No live transfer yet.) |
| `log_complaint(type, details)` | all | Logs a complaint/hardship event. |
| `log_payment_promise(date, amount, reason)` | Neha | Logs a promise-to-pay. **Stub** — no CRM write. |
| `create_payment_request(amount, upi_id)` | Neha | Returns a fake payment link. **Stub** — no Razorpay. |

---

## 4. What changed in this pass (2026-06-16)

Cleanup to make the project a solid base to build on:

- **Centralized the pipeline** in `services/pipeline.py`; `main.py` no longer
  hard-codes models.
- **Prewarm the VAD** once per process (was reloading Silero on every call).
- **Robust config** via `proc.userdata` (was fragile module globals only set in
  `__main__`).
- **Added multilingual turn detection** (dependency existed but was unused).
- **Wired the payment tools** into Neha — they were dead code before.
- **Tunable models/voice from `.env`** (STT/LLM/TTS/voice/speed/turn-detector).
- **Fixed the stale README** (it claimed Claude/Anthropic; the code uses Gemini)
  and added `.gitignore`.

---

## 5. Production gaps (what's NOT real yet)

| Area | Status | What's needed |
|------|--------|---------------|
| **Telephony** | ❌ Playground only | LiveKit SIP trunk + phone number for real PSTN calls. |
| **CRM** | ⚠️ Mocked | Replace `services/mock_crm.py` with the real driver/loan API or DB. |
| **Payments** | ⚠️ Stubbed | Implement `tools/payment.py` against Razorpay + write-back to CRM. |
| **Human transfer** | ⚠️ Logs only | `transfer_to_human` should warm-transfer/SIP-refer to a live agent. |
| **Outbound dialing** | ❌ Missing | A dispatcher that places calls (cron/queue) → creates rooms with driver metadata. |
| **Persistence** | ⚠️ Local file | `call_events.jsonl` is local; move to a DB/warehouse for reporting. |
| **Tests** | ❌ None | Add unit tests (mock_crm matching, config, scenario templating) + eval harness for prompts. |
| **Secrets** | ⚠️ `.env` | Move to a secrets manager for production. |

---

## 6. Suggested roadmap (in order)

1. **Real CRM read** — swap `mock_crm.py` for the live lookup so calls use real
   driver/loan data (driver phone → profile, scenario derived from due date).
2. **Razorpay write** — implement `tools/payment.py`; log promises + links back
   to the CRM.
3. **Telephony** — provision a LiveKit SIP trunk + number; pass the driver's
   phone/metadata as room metadata so `entrypoint` can look them up.
4. **Outbound dispatcher** — a scheduler that decides who to call (which
   scenario) and creates the dispatch jobs.
5. **Observability** — ship `call_events` to a DB; add a dashboard
   (connect rate, promise rate, escalations).
6. **Prompt evals** — a regression harness so prompt edits can be tested without
   live calls.

---

## 7. Gotchas

- **`python main.py download-files`** must be run once, or the turn detector
  fails at runtime. To skip turn detection entirely, set `USE_TURN_DETECTOR=false`.
- **Scenario selection** is driven by the fixture/`.env`, not auto-derived from
  the date. When CRM is wired, derive A/B/C from days-relative-to-due-date.
- **Money must stay phonetic** in prompts for correct Hindi TTS — don't replace
  `तीन सौ रुपये` with `₹300`.
- `mock_crm` matches a fixture by **room name** (or phone number); with no match
  it falls back to `TEST_*` env vars, then hard-coded defaults.
- There is a `SARVAM_API_KEY` in `.env` but **nothing uses Sarvam** in code yet —
  it's a leftover/experiment.
