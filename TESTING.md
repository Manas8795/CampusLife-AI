# CampusLife AI — Testing Guide

## Test Strategy

CampusLife AI follows a **three-tier testing strategy** aligned with the Testing Pyramid:

```
         ┌──────────────┐
         │   E2E Tests  │  ← Simulate full HTTP roundtrip (pytest + FastAPI TestClient)
         ├──────────────┤
         │ Integration  │  ← Test DB + Service layer together with seeded data
         ├──────────────┤
         │  Unit Tests  │  ← Fast, isolated, zero external dependencies
         └──────────────┘
```

---

## Test Files

| File | Type | What it Covers |
|---|---|---|
| `tests/test_modules_1_to_6.py` | E2E | All 6 domain modules via HTTP |
| `tests/test_module_7.py` | E2E | Voice agent, calls, WebSocket |
| `tests/test_module_8.py` | Integration | AI infrastructure endpoints |
| `tests/test_unit_voice_agent.py` | **Unit** | Intent detection (30+ cases), Command Registry, Observer Pattern, Strategy Chain |
| `tests/test_unit_expense_classifier.py` | **Unit** | Expense category classifier (all 8 categories + edge cases) |

---

## Running Tests

### Full Suite
```bash
# From project root
pytest tests/ -v
```

### Unit Tests Only (fast, no DB needed)
```bash
pytest tests/test_unit_voice_agent.py tests/test_unit_expense_classifier.py -v
```

### With Coverage Report
```bash
pytest tests/ --cov=backend/app --cov-report=term-missing --cov-report=html
open htmlcov/index.html   # View interactive coverage report
```

### Specific Test Class
```bash
pytest tests/test_unit_voice_agent.py::TestIntentCommandRegistry -v
```

---

## Before Running: Seed the Database
```bash
python -m backend.seed_data
```

---

## Coverage Targets

| Module | Target | Rationale |
|---|---|---|
| `voice/agent.py` | ≥ 85% | Core intent logic — highest complexity |
| `voice/llm_strategy.py` | ≥ 90% | Strategy pattern — new code |
| `voice/intent_commands.py` | ≥ 80% | Command pattern — new code |
| `voice/alert_observer.py` | ≥ 85% | Observer pattern — new code |
| `tools/campuslife_tools.py` | ≥ 70% | Core tool layer |
| **Overall** | **≥ 60%** | CI/CD gate (enforced in ci.yml) |

---

## Mocking External Dependencies

Tests that would otherwise require a live Ollama server, Twilio, or Telegram
use `unittest.mock.patch` to stub out external calls:

```python
# Example: Disable Ollama during unit tests
with patch("urllib.request.urlopen", side_effect=Exception("offline")):
    result = strategy.generate("prompt", "system")
assert result is None  # Gracefully returns None when offline
```

---

## Test Environment Variables

Required for CI (see `.github/workflows/ci.yml`):

```bash
SECRET_KEY=ci-test-secret-key
TWILIO_ACCOUNT_SID=AC_CI_DUMMY
TWILIO_AUTH_TOKEN=ci_dummy_token
TWILIO_PHONE_NUMBER=+10000000000
TELEGRAM_BOT_TOKEN=0000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
TELEGRAM_CHAT_ID=0
```

---

## Test Design Principles

1. **Arrange → Act → Assert** structure throughout
2. **Parametrize** repetitive cases instead of duplicating test functions
3. **Isolate** — unit tests have no external I/O (DB, network, file system)
4. **Name clearly** — test names describe the scenario, not the implementation
5. **Test edge cases** — empty strings, zero values, malformed inputs
6. **Test negative paths** — wrong intent, blocked policy, unavailable provider
