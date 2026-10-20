# CampusLife AI — Unified Autonomous Student Intelligence Co-Pilot

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black.svg)](https://threejs.org/)
[![Tests](https://img.shields.io/badge/tests-140%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> An autonomous, proactive, cross-domain student intelligence co-pilot and web platform. Rather than forcing students to juggle fragmented apps for study planning, wellness tracking, personal finance, travel logistics, and reminders, CampusLife AI unifies all dimensions under a single relational schema, autonomous cross-domain reasoning, and full-duplex voice interaction.

---

## 🌟 Key Features

### 1. 🧠 Cross-Domain Student Intelligence Engine ("Compound Overload" Detection)
- Correlates academic deadlines, sleep deficits, caffeine/energy drink spending spikes, and travel schedules in real time.
- Predicts burnout probability before it happens (e.g. 3 exams due in 48h + < 5.5 hours sleep $\rightarrow$ suggests tactical rescheduling).
- Autonomous background sentinel monitors student state continuously and triggers interventions.

### 2. 🎙️ Full-Duplex AI Voice Assistant & Telephony Co-Pilot
- Real-time conversational AI powered by local LLM (`llama3.2:1b` via Ollama) with multi-model cloud fallbacks.
- Native tool execution: query schedules, log sleep & mood, add study tasks, review financial runway, check exam conflicts.
- **3D Interactive Voice Orb**: WebGL audio resonator reacting dynamically to microphone input and TTS speech synthesis.
- **Mobile Calling Interface (`/call`)**: Simulated SIP & real-time mobile standby screen that rings your phone with low latency.
- Telegram Bot broadcaster for urgent academic alerts.

### 3. 🎨 Bespoke Design System & 5 Themes
- Unified collapsible navigation sidebar (`Ctrl+B` toggle, state persistence across pages).
- **5 Handcrafted Themes**:
  - **Alabaster (Default)**: Clean, high-legibility light mode with sapphire accents.
  - **Midnight Obsidian**: Deep cosmic dark mode.
  - **Cyberpunk Neon**: High-contrast vibrant cyberpunk palette.
  - **Emerald Matrix**: Terminal-inspired dark emerald theme.
  - **Solar Sunset**: Warm evening amber & rose palette.

### 4. 📚 8 Integrated Subsystems
| Subsystem | Endpoint | Capabilities |
| :--- | :--- | :--- |
| **Analytics Hub** | `/` | 3D academic scene (Three.js), vitality distribution, time allocation |
| **To-Do & Study Planner** | `/study` | Interactive monthly calendar, task priority ledger, AI pacing plans |
| **Health & Wellness** | `/health` | Sleep & vitals logging, rolling 7-day baselines, ML stress heuristic |
| **Financial Manager** | `/expenses` | Budget tracking, receipt OCR ingestion sandbox, burn rate & runway |
| **Travel & Logistics** | `/travel` | Trip planner, AI itinerary generator, automatic exam conflict shield |
| **Intelligence Engine** | `/intelligence` | Cross-domain causality analysis, risk score matrix, anomaly detection |
| **Voice Co-Pilot** | `/voice` | Web Speech STT/TTS studio, audio spectrum visualizer, intent routing |
| **AI/ML Infrastructure**| `/infra` | Local LLM testbed, RAG vector memory explorer, model registry |

---

## 🏛️ System Architecture

```text
                               ┌─────────────────────────────────────────┐
                               │           CampusLife Web Client         │
                               │  (Vanilla JS + Three.js + Chart.js)     │
                               └────────────────────┬────────────────────┘
                                                    │ REST & WebSockets
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Application                                  │
├──────────────────┬──────────────────┬──────────────────┬───────────────────────────────┤
│ Core & Auth      │ Study & Tasks    │ Health & Vitals  │ Expense & OCR Engine          │
├──────────────────┼──────────────────┼──────────────────┼───────────────────────────────┤
│ Travel Shield    │ Intelligence     │ Voice Agent      │ Autonomous Sentinel Loop      │
└──────────────────┴─────────┬────────┴─────────┬────────┴───────────────────────────────┘
                             │                  │
                ┌────────────┴────────┐   ┌─────┴──────────────────┐
                │  SQLAlchemy ORM     │   │ AI & Speech Engines    │
                │  (SQLite Database)  │   │ - Local Ollama / Groq  │
                └─────────────────────┘   │ - Web Speech API       │
                                          │ - Telegram / Twilio    │
                                          └────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+** installed
- *(Optional)* [Ollama](https://ollama.ai/) with `llama3.2:1b` model running locally on `http://127.0.0.1:11434`

### 1. Clone the Repository
```bash
git clone https://github.com/Manas8795/CampusLife-AI.git
cd CampusLife-AI
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy sample configuration
cp .env.example .env
```
*(Default settings use SQLite and local simulated telephony out of the box — no external paid API keys required!)*

### 4. Initialize Database Seed Data
```bash
python -m backend.seed_data
```

### 5. Start the Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.  
Interactive OpenAPI documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 📱 Mobile Phone Voice Setup

To test the mobile phone voice standby call screen on your actual smartphone:

1. **Option A: Same Wi-Fi / Hotspot (Direct LAN)**
   - Find your PC IP (e.g. `192.168.1.X` or `172.20.168.148`).
   - Open `http://<YOUR_IP>:8000/static/mobile_call.html` in your phone browser.

2. **Option B: Secure HTTPS Cloudflare Quick Tunnel (Recommended for Microphones)**
   - Download `cloudflared`:
     ```bash
     .\cloudflared.exe tunnel --url http://127.0.0.1:8000
     ```
   - Open the generated `https://<subdomain>.trycloudflare.com/static/mobile_call.html` link on your phone. iOS and Android will instantly grant mic permissions over HTTPS.

---

## 🧪 Testing & Code Quality

The suite includes comprehensive unit and integration tests covering all 8 modules, cross-domain causal reasoning, and telephony engines:

```bash
# Run all tests with coverage report
pytest -v --cov=backend/app --cov-report=term-missing
```

**Results:**
- **140 / 140 passed** in `< 4 seconds`
- Zero regressions across core intelligence, voice strategies, and calendar scheduling logic.

---

## 📂 Project Directory Structure

```text
CampusLife-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI initialization & routing
│   │   ├── config.py                # Pydantic BaseSettings & credentials
│   │   ├── database.py              # SQLAlchemy engine & session factory
│   │   ├── core/                    # Authentication, users & profiles
│   │   ├── study/                   # Tasks, calendar & AI pacing
│   │   ├── health/                  # Sleep, mood & stress heuristic
│   │   ├── expenses/                # Budget, runway forecast & OCR
│   │   ├── travel/                  # Trips, itineraries & exam conflict shield
│   │   ├── intelligence/            # Compound risk & cross-domain synthesis
│   │   ├── voice/                   # Speech agent, intent router & telephony
│   │   ├── infra/                   # LLM engine, RAG memory & model registry
│   │   └── static/                  # Vanilla JS frontend, 3D WebGL & styles
│   ├── seed_data.py                 # Comprehensive seed generator
│   ├── export_and_clear_db.py       # DB export utility
│   └── restore_from_csv.py          # Data ingestion utility
├── tests/                           # Pytest test suite (140 tests)
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore configuration
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Multi-stage production Dockerfile
├── docker-compose.yml               # Production container orchestration
├── LICENSE                          # MIT License
└── README.md                        # Master project documentation
```

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE) © 2026 Manas Agrawal.
