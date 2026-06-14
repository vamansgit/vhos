# VHOS v2.4 — Local Setup Guide

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Python | 3.11 | https://python.org/downloads |
| Git | any | https://git-scm.com |
| Redis | 6+ | see below |

Redis is optional — VHOS falls back to in-memory storage automatically if Redis is not running.

---

## 1. Clone the repo

```bash
git clone https://github.com/vamansgit/vhos.git
cd vhos
git checkout claude/laughing-cannon-afibbl
```

---

## 2. Create a Python virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows
```

---

## 3. Install dependencies

```bash
pip install -e ".[dev]"
```

---

## 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
# Required for Claude Haiku intent classification (optional — keyword fallback works without it)
ANTHROPIC_API_KEY=sk-ant-...

# Leave everything else as-is for demo mode
USE_DEMO_DATA=true
```

The app runs fully without an API key — it uses keyword-based intent classification as fallback.

---

## 5. Generate demo data

```bash
python demo_data/generate.py
```

This creates 10 Excel files in `demo_data/` with synthetic patients, appointments, labs, etc.

---

## 6. Run the interactive CLI

```bash
chmod +x vhos.sh
./vhos.sh
```

The script starts the server automatically and opens a chat prompt.

### CLI modes

```bash
./vhos.sh            # interactive chat
./vhos.sh demo       # automated demo (5 scenarios, no input needed)
./vhos.sh agents     # list all 43 agents
./vhos.sh stop       # stop the background server
```

### Chat commands

| Type this | What happens |
|-----------|-------------|
| `book an appointment` | Appointment scheduling flow |
| `I have chest pain` | Emergency escalation (<1 second) |
| `I feel hopeless and sad` | PHQ-9 mental health screening |
| `check my insurance` | Coverage + co-pay lookup |
| `what are cardiology timings` | Department info |
| `I have a fever` | MTS triage protocol |
| `/new provider` | Switch to provider auth (nurse/doctor copilot) |
| `/new medium` | Switch back to patient auth |
| `/audit` | Show last 5 HMAC-chained audit entries |
| `/agents` | List all agents grouped by pillar |
| `/demo` | Run 4 quick scenarios inline |
| `/quit` | Exit |

---

## 7. (Optional) Start the server manually

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open **http://localhost:8000/docs** for the full Swagger UI.

---

## 8. (Optional) Install Redis

### Mac
```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### Windows
```bash
# Use Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

Then in `.env` set:
```env
REDIS_URL=redis://localhost:6379/0
```

---

## 9. Run tests

```bash
pytest tests/ -v
```

All 34 tests should pass.

---

## 10. Docker (alternative to steps 2–6)

```bash
cp .env.example .env   # edit ANTHROPIC_API_KEY if desired
docker compose up
```

Then use the CLI against the running container:

```bash
BASE=http://localhost:8000 ./vhos.sh
```

---

## API quick reference

```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"UHID-1001","auth_level":"medium"}'

# Send message  (replace SESSION_ID)
curl -X POST http://localhost:8000/session/SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d '{"message":"book an appointment"}'

# One-shot (no session needed)
curl -X POST http://localhost:8000/demo/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I have chest pain","auth_level":"medium"}'
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python3.11` | Install Python 3.11 from python.org |
| `ModuleNotFoundError` | Make sure venv is activated and `pip install -e .` ran |
| Server won't start | Check `/tmp/vhos.log` for errors |
| Port 8000 in use | `lsof -i:8000` then kill the PID, or change port in `vhos.sh` |
| Redis connection error | Ignored automatically — app uses in-memory fallback |
