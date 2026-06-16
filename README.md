# Chargeup Voice Agent

AI-powered outbound voice agents for Chargeup EV battery finance, built for
Hindi-speaking e-rickshaw drivers in India (Hinglish conversations).

Two agents share one platform:
- **Neha** — collections (payment reminders, 3 scenarios + objection handling)
- **Khushi** — sales (lead qualification + battery pitch)

**Stack:** LiveKit Agents 1.5 · Deepgram STT (`nova-3`) · Google Gemini
(`gemini-2.5-flash`) · Cartesia TTS (`sonic-3`, Hindi) · Silero VAD ·
multilingual turn detector.

---

## Project structure

```
chargeup-voice-agent/
├── main.py                     ← worker entry point (prewarm + entrypoint)
├── agents/
│   ├── base_agent.py           ← ChargeupBaseAgent: Hinglish rules + shared tools
│   │                             (hangup, transfer_to_human, log_complaint)
│   ├── collections_agent.py    ← Neha — scenarios A/B/C, objections, payment tools
│   └── sales_agent.py          ← Khushi — lead qualification + locked product/pricing
├── services/
│   ├── config.py               ← env validation + tunable pipeline settings
│   ├── pipeline.py             ← builds the STT/LLM/TTS/VAD/turn-detect session
│   ├── events.py               ← JSON-Lines call-event logging
│   └── mock_crm.py             ← driver lookup (fixture → env → defaults)
├── tools/
│   └── payment.py              ← payment-link / promise-to-pay stubs (wire Razorpay here)
├── mock_data/drivers.json      ← 6 test fixtures (collections + sales)
├── runtime/                    ← call_events.jsonl is written here
├── requirements.txt
└── .env.example                ← copy to .env and fill in keys
```

---

## Setup (one time)

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

cp .env.example .env             # then fill in the 6 required keys
python main.py download-files    # one-time: download the turn-detector model
```

### Required keys

| Key | Where |
|-----|-------|
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | cloud.livekit.io → project → Settings |
| `DEEPGRAM_API_KEY` | console.deepgram.com → API Keys |
| `GOOGLE_API_KEY` | aistudio.google.com → API Keys (Gemini) |
| `CARTESIA_API_KEY` | play.cartesia.ai → API Keys |

---

## Run locally

```bash
python main.py dev
```

Then open https://agents-playground.livekit.io → connect to your project →
**Connect** → speak. The agent (Neha or Khushi) is chosen from the matched
`mock_data/drivers.json` fixture; with no match it falls back to the `TEST_*`
env vars.

### Pick which driver/scenario to test

The fixture is matched by **room name**. Join a room named after a fixture:

| Room name | Agent | Notes |
|-----------|-------|-------|
| `dev-ramesh` | Neha | Scenario A (before due) |
| `dev-sunita` | Neha | Scenario B (on due date) |
| `dev-salman` | Neha | Scenario C (overdue) |
| `sales-default` / `sales-rto` / `sales-ad` | Khushi | DEFAULT / RTO_LEAD / AD_LEAD |

No matching room → the `TEST_*` values in `.env` are used instead.

---

## How it works

1. `prewarm()` runs once per worker process: validates config, loads the Silero
   VAD a single time, and creates the event logger — all stored on
   `proc.userdata`.
2. `entrypoint()` runs per call: looks up the driver (`services/mock_crm.py`),
   builds the matching agent, and builds the voice session via
   `services/pipeline.py::build_session()`.
3. All notable actions (call received, escalation, complaint, payment promise)
   are appended to `runtime/call_events.jsonl`.

To swap a model or voice, change the values in `.env` — no code edits needed.

---

## Next steps

See [docs/HANDOFF.md](docs/HANDOFF.md) for the engineering handoff, the
production gaps, and the prioritized roadmap (telephony/SIP, real CRM, Razorpay).
