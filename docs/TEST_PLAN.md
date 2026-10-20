# CampusLife AI — Master Test Plan (IEEE 829 Format)

**Document Version:** 2.0  
**Status:** Approved & Verified  
**Test Suite Pass Rate:** 100% (139 / 139 tests passing)  
**Total Statements Covered:** 2,551+ statements (64% total codebase branch coverage)  

---

## 1. Introduction & Objectives

### 1.1 Purpose
This document defines the comprehensive software verification and validation strategy for **CampusLife AI**, an autonomous multimodal student co-pilot. The testing strategy evaluates correctness, real-time performance, fault tolerance, and security across 8 software engineering modules.

### 1.2 Test Scope
| Module | Name | Testing Focus |
|---|---|---|
| **Module 1** | Core & Auth | JWT auth, profile management, preferences, notifications |
| **Module 2** | Study Planner | Task CRUD, status transitions, productivity delay risk |
| **Module 3** | Health & Wellness | Sleep logs, stress prediction, circadian recommendations |
| **Module 4** | Financial Manager | Expense tracking, taxonomy classifier, burn-rate forecast |
| **Module 5** | Travel Planner | Itinerary planning, academic conflict detection |
| **Module 6** | Student Intelligence | Cross-domain compound overload, causality engine, life balance |
| **Module 7** | Voice & Telephony | Intent extraction, command registry, strategy chain, alert observers |
| **Module 8** | AI/ML & Infra | Health endpoints, telemetry, OCR & ML serving mock interfaces |

---

## 2. Test Strategy & Architecture

CampusLife AI implements a **Three-Tier Testing Pyramid**:

```
                 ┌───────────────────┐
                 │    E2E Tests      │   ← Real Voice Flow & Telephony Sim
                 ├───────────────────┤
                 │ Integration Tests │   ← FastAPI TestClient & DB Fixtures
                 ├───────────────────┤
                 │    Unit Tests     │   ← Pure logic, Zero External I/O
                 └───────────────────┘
```

### 2.1 Unit Testing Tier (`tests/test_unit_voice_agent.py`, `tests/test_unit_expense_classifier.py`)
- **Isolation Principle**: Pure functions executed with zero network, database, or filesystem dependencies.
- **Parametrized Intent Tests**: 35+ voice phrases validating exact intent extraction across all student actions.
- **Expense Taxonomy Classifier**: 40+ real campus expense phrases mapped to 8 taxonomical categories using maximum-length keyword disambiguation.
- **Calling Policy Engine**: Boundary testing for quiet hours (`22:00` to `08:00`), opt-in consent, and frequency limits.
- **Design Pattern Unit Verification**:
  - Strategy Pattern: Fallback chain ordering (`Ollama` → `OpenAI` → `LocalDomainStrategy`).
  - Observer Pattern: Unsubscribe, error isolation, independent dispatching.
  - Command Pattern: Registry registration, dispatch validity, execution idempotency.

### 2.2 Integration Testing Tier (`tests/test_modules_1_to_6.py`, `tests/test_module_7.py`, `tests/test_module_8.py`)
- **Database State Fixtures**: Seeded database mimicking Alex Sharma's active semester (NIT CSE).
- **FastAPI TestClient**: Full HTTP request/response cycle verification including schema validation with Pydantic v2.
- **Cross-Domain Intelligence Verification**: Testing that simultaneous low sleep (< 5.5h) and imminent assignments (> 3) trigger compound overload alerts.

---

## 3. Test Cases & Execution Matrix

### 3.1 Unit Test Suites
| Suite | File | Tests | Status |
|---|---|---|---|
| Voice Intent Parametrized | `tests/test_unit_voice_agent.py` | 35 | ✅ PASS |
| Parameter Extraction (Expense/Task/Sleep) | `tests/test_unit_voice_agent.py` | 15 | ✅ PASS |
| Calling Policy Engine | `tests/test_unit_voice_agent.py` | 4 | ✅ PASS |
| LLM Strategy Chain | `tests/test_unit_voice_agent.py` | 5 | ✅ PASS |
| Alert Observer Pattern | `tests/test_unit_voice_agent.py` | 3 | ✅ PASS |
| Intent Command Registry | `tests/test_unit_voice_agent.py` | 5 | ✅ PASS |
| Expense Category Classifier | `tests/test_unit_expense_classifier.py` | 47 | ✅ PASS |
| **Total Unit Tests** | | **114** | **100% PASS** |

### 3.2 Integration Test Suites
| Suite | File | Tests | Status |
|---|---|---|---|
| Modules 1 to 6 Full Stack | `tests/test_modules_1_to_6.py` | 8 | ✅ PASS |
| Module 7 Voice & Telephony | `tests/test_module_7.py` | 10 | ✅ PASS |
| Module 8 AI/ML Infrastructure | `tests/test_module_8.py` | 7 | ✅ PASS |
| **Total Integration Tests** | | **25** | **100% PASS** |

---

## 4. Test Execution Instructions

### 4.1 Running All Unit Tests
```bash
python -m pytest tests/test_unit_voice_agent.py tests/test_unit_expense_classifier.py -v
```

### 4.2 Running Full Test Suite
```bash
python -m pytest -v --tb=short
```

### 4.3 Generating Code Coverage Report
```bash
python -m pytest --cov=backend/app --cov-report=term-missing --cov-report=json:coverage.json tests/
```

---

## 5. Defect Management & Resolution Log

| Issue ID | Module | Description | Resolution | Status |
|---|---|---|---|---|
| **BUG-01** | `agent.py` | Dead code in intent dispatcher after return | Refactored into `IntentCommand` pattern | ✅ FIXED |
| **BUG-02** | `llm_engine.py` | Unreachable LM Studio fallback after cache return | Pluggable Strategy Pattern implementation | ✅ FIXED |
| **BUG-03** | `deadline_watcher.py` | In-memory notification state lost on restart | Persistent DB-backed state + Observer pattern | ✅ FIXED |
| **BUG-04** | `campuslife_tools.py` | Keyword shadowing in classifier (`ticket` vs `movie ticket`) | Descending length keyword matching strategy | ✅ FIXED |
| **BUG-05** | `voice/agent.py` | Inquiries missing regex prefixes for `what tasks...` | Added comprehensive read inquiry intent rules | ✅ FIXED |
