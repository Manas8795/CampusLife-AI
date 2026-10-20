# CampusLife AI — System Design Document (SDD)

**Version:** 2.0 | **Document Type:** System Design Document

---

## 1. Architecture Overview

CampusLife AI follows a **Layered Architecture** with 4 tiers:

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                           │
│   Browser Dashboard  │  Mobile Call UI (WebSocket)  │  REST API      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ HTTP / WebSocket
┌────────────────────────────────▼─────────────────────────────────────┐
│                           API Layer (FastAPI)                        │
│  core/router  │  study/router  │  health/router  │  voice/router     │
│  expenses/router  │  travel/router  │  intelligence/router           │
│  + CorrelationIDMiddleware  │  + CORSMiddleware                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ Function calls
┌────────────────────────────────▼─────────────────────────────────────┐
│                        Service Layer                                 │
│  StudyService  │  HealthService  │  ExpenseService  │  TravelService │
│  IntelligenceService  │  VoiceAgent  │  LocalStudentLLM              │
│  + Strategy Pattern (LLM)  │  + Command Pattern (Intent Dispatch)   │
│  + Observer Pattern (Alerts)  │  + Policy Engine (Call Gating)      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ ORM queries
┌────────────────────────────────▼─────────────────────────────────────┐
│                        Data Layer (SQLAlchemy + SQLite)              │
│  User  │  Task  │  HealthRecord  │  Expense  │  Trip  │  VoiceCall  │
│  StudentState  │  sentinel_alert_log                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Patterns Applied

### 2.1 Strategy Pattern — LLM Provider Selection
**Location:** `backend/app/voice/llm_strategy.py`

**Intent:** Define a family of LLM provider algorithms, encapsulate each, and make them interchangeable. The provider can vary independently from the client.

```
LLMStrategy (ABC)
├── OllamaStrategy       — Local Ollama server (llama3.2:1b, phi3…)
└── OpenAIStrategy       — Cloud API (gpt-4o-mini)

LocalStudentLLM:
  strategy_chain = [OllamaStrategy, OpenAIStrategy]  ← priority order
  for strategy in strategy_chain:
      result = strategy.generate(prompt, system)
      if result: return result
  # Fallback: guaranteed local domain engine
```

**Benefits:**
- Open/Closed Principle: new providers added without modifying `LocalStudentLLM`
- Testable: each strategy can be tested in isolation with mocked network
- Configurable: chain composition driven by environment settings

---

### 2.2 Observer Pattern — Alert Notification System
**Location:** `backend/app/voice/alert_observer.py`

**Intent:** Define a one-to-many dependency so that when the Subject (Sentinel) fires an alert, all registered Observers are notified automatically.

```
AlertSubject (mixin) ──── notify(AlertEvent)
         │
         ├── WebSocketAlertObserver   → broadcasts INCOMING_CALL to mobile UI
         └── LogAlertObserver         → writes structured log entry

AutonomousSentinelWatcher
  ├── inherits AlertSubject
  ├── subscribe(WebSocketAlertObserver)
  ├── subscribe(LogAlertObserver)
  └── checks deadlines/sleep → await self.notify(AlertEvent)
```

**Benefits:**
- Loose coupling: Sentinel knows nothing about WebSocket internals
- Extensible: Telegram, email, SMS observers added with zero changes to Sentinel
- Fault isolation: one failing observer never blocks others (`asyncio.gather`)

---

### 2.3 Command Pattern — Voice Intent Dispatch
**Location:** `backend/app/voice/intent_commands.py`

**Intent:** Encapsulate each voice intent as a Command object, allowing the dispatcher to be decoupled from the specific action implementation.

```
IntentCommand (ABC)
├── LogExpenseCommand      → campuslife_tools.log_expense()
├── CreateTaskCommand      → campuslife_tools.create_task()
├── GetWellnessCommand     → campuslife_tools.get_wellness_state()
└── ... (16 total)

INTENT_REGISTRY: Dict[str, Type[IntentCommand]] = {
    "LOG_EXPENSE": LogExpenseCommand,
    ...
}

# Dispatcher (replaces 15-branch if/elif):
execute_intent(intent, user_id, params)
  → INTENT_REGISTRY[intent]().execute(user_id, params)
```

**Benefits:**
- Open/Closed Principle: new intents added as new Command subclasses
- Single Responsibility: each Command owns exactly one tool interaction
- Testable: each Command independently instantiable and testable

---

## 3. Module-Level Component Diagram

```
┌──────────────────────────────────────────────────────┐
│                     Module 7                         │
│  Voice Router → VoiceAgent → detect_intent()         │
│                      │                               │
│                      ▼                               │
│              execute_intent()  ← INTENT_REGISTRY     │
│           (Command Pattern)          │               │
│                      │               ▼               │
│                      ▼         IntentCommand         │
│           campuslife_tools      subclasses           │
│        (unified tool layer)                          │
│                      │                               │
│                      ▼                               │
│          LocalStudentLLM.generate_student_response() │
│           (Strategy Pattern — LLM Chain)             │
│                                                      │
│  AutonomousSentinelWatcher                           │
│    (Observer Subject)                                │
│    │                                                 │
│    ├── WebSocketAlertObserver → mobile_call_manager  │
│    └── LogAlertObserver       → structured logs      │
│                                                      │
│  CallingPolicyEngine                                 │
│    ├── Consent check                                 │
│    ├── Quiet hours enforcement                       │
│    ├── 4-hour cooldown                               │
│    └── Compound risk threshold                       │
└──────────────────────────────────────────────────────┘
```

---

## 4. Voice Query Sequence Diagram

```
Student (Mobile)          VoiceRouter           VoiceAgent          LLMEngine          DB
      │                        │                     │                    │              │
      │── POST /voice/message ►│                     │                    │              │
      │                        │── process_turn() ──►│                    │              │
      │                        │                     │── detect_intent() ─┤              │
      │                        │                     │◄── (intent, params)┤              │
      │                        │                     │── execute_intent() ┤              │
      │                        │                     │   [Command Registry]│              │
      │                        │                     │─────────── tool call ────────────►│
      │                        │                     │◄─────────── tool_data ────────────│
      │                        │                     │── generate_response()─►           │
      │                        │                     │   [Strategy Chain]    │            │
      │                        │                     │◄── LLM text ──────────│            │
      │◄────── JSON response ──│◄── {reply, intent} ─┤                    │              │
      │  {assistant_reply,     │                     │                    │              │
      │   intent_detected,     │                     │                    │              │
      │   tool_executed,       │                     │                    │              │
      │   engine, latency_ms}  │                     │                    │              │
```

---

## 5. Proactive Call Activity Diagram

```
[Sentinel Loop — every 4s]
         │
         ▼
  Check Deadlines
         │
    task.due_date <= now
    AND status PENDING?
         │
        YES ──► _has_been_notified(DB)? ──YES──► Skip
         │             │
         │            NO
         │             ▼
         │       _mark_notified(DB)
         │       task.status = OVERDUE
         │             │
         │       ◄── notify(AlertEvent)
         │         │               │
         │   WebSocket          LogObserver
         │   Observer
         │         │
         │   mobile_call_manager.broadcast()
         │         │
         │   Mobile UI rings 📱
         │
  Check Sleep / Health
         │
    sleep_hours < 6.0
    OR stress HIGH
    OR mood+energy low?
         │
        YES ──► _has_been_notified(DB)? ──YES──► Skip
                      │
                     NO
                      ▼
                _mark_notified(DB)
                notify(AlertEvent)
```

---

## 6. Database Entity-Relationship Overview

```
User (1)────────────(1) Profile
  │
  ├──(1)────────────(1) UserPreference
  │
  ├──(1)────────(many) Task
  │
  ├──(1)────────(many) HealthRecord
  │
  ├──(1)────────(many) Expense
  │
  ├──(1)────────(many) Budget
  │
  ├──(1)────────(many) Trip ──(1)──(many) TripItineraryItem
  │
  ├──(1)────────(many) VoiceCall
  │
  ├──(1)────────(many) Conversation ──(1)──(many) ConversationMessage
  │
  └──(1)────────────(1) StudentState

sentinel_alert_log (standalone — alert_key PK, fired_at)
```

---

## 7. Observability Architecture

```
HTTP Request
     │
     ▼
CorrelationIDMiddleware
  generates UUID → ContextVar[correlation_id]
     │
     ▼
All log.info() calls automatically include correlation_id
     │
     ▼
StructuredJSONFormatter
  → {"ts":"...", "level":"INFO", "logger":"campuslife.agent",
      "correlation_id":"abc-123", "msg":"intent_dispatched",
      "intent":"GET_TASKS", "user_id":1}
     │
     ▼
stdout → collected by container runtime / log aggregator (e.g. CloudWatch, Loki)
```

---

## 8. Security Architecture

| Threat | Mitigation |
|---|---|
| Credential exposure in source | All secrets in `.env` only; defaults removed from `config.py` |
| Unauthorized calling | Consent check + quiet hours + cooldown in `CallingPolicyEngine` |
| Replay attacks | JWT exp claim + 7-day token rotation |
| Cross-origin requests | CORS middleware (tightened to known origins in production) |
| LLM injection | System prompt constraints + Hindi interceptor |
