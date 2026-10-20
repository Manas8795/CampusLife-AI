# CampusLife AI — Software Requirements Specification (SRS)
**Version:** 2.0 | **Document Type:** SRS (IEEE 830 Format) | **Module Count:** 8

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for **CampusLife AI**, an AI-powered student co-pilot platform providing proactive academic, wellness, financial, and travel management through a conversational voice agent and real-time mobile interface.

### 1.2 Scope
CampusLife AI consists of 8 integrated modules deployed as a FastAPI backend with a WebSocket-driven mobile frontend:
- **M1:** Platform Core & User Management
- **M2:** To-Do & Study Planner
- **M3:** Health & Wellness Monitoring
- **M4:** Expense & Financial Manager
- **M5:** Travel & Trip Planner
- **M6:** Student Intelligence Engine
- **M7:** AI Voice Assistant & Calling System
- **M8:** AI/ML Infrastructure & Deployment

### 1.3 Definitions
| Term | Definition |
|---|---|
| **Compound Risk Score** | Weighted aggregation of academic, wellness, and financial risk signals (0.0–1.0) |
| **Proactive Call** | Autonomous outbound AI alert triggered by the Sentinel Watcher |
| **Quiet Hours** | User-configured time window during which proactive calls are suppressed |
| **Intent** | Classified semantic category of a user's voice query (e.g., GET_TASKS, LOG_EXPENSE) |
| **Strategy Chain** | Ordered list of LLM providers tried in sequence until one succeeds |

---

## 2. Functional Requirements

### Module 1: Platform Core & User Management
| ID | Requirement |
|---|---|
| FR-1.1 | System shall authenticate users via email/password and return a JWT access token |
| FR-1.2 | System shall maintain a user profile (name, college, major, graduation year) |
| FR-1.3 | System shall store per-user preferences: quiet hours, voice call consent, currency |
| FR-1.4 | System shall provide a unified dashboard aggregating data from all domain modules |
| FR-1.5 | System shall support Quick-Add shortcuts for tasks and expenses from the dashboard |

### Module 2: To-Do & Study Planner
| ID | Requirement |
|---|---|
| FR-2.1 | System shall create, read, update, and delete academic tasks |
| FR-2.2 | Each task shall have: title, subject, priority (LOW/MEDIUM/HIGH), status, due date |
| FR-2.3 | System shall classify tasks as OVERDUE when due_date has passed and status is PENDING |
| FR-2.4 | System shall compute a productivity risk score (LOW/MEDIUM/HIGH) based on overdue ratio and task backlog |
| FR-2.5 | System shall support voice-driven task creation with natural language due date parsing |

### Module 3: Health & Wellness
| ID | Requirement |
|---|---|
| FR-3.1 | System shall record daily sleep hours, mood (1–5), energy level (1–5), and notes |
| FR-3.2 | System shall compute a 7-day rolling sleep average against a personal baseline |
| FR-3.3 | System shall predict current stress level (LOW/MEDIUM/HIGH) from wellness signals |
| FR-3.4 | System shall classify sleep status as HEALTHY (≥7h) or BELOW_BASELINE (<7h) |
| FR-3.5 | System shall provide mindfulness recommendations (breathing exercises, study breaks) |

### Module 4: Expense & Financial Manager
| ID | Requirement |
|---|---|
| FR-4.1 | System shall record expenses with amount, category, description, merchant, payment method |
| FR-4.2 | System shall classify expenses into 8 categories: Academic, Food, Transport, Entertainment, Health, Shopping, Travel, Other |
| FR-4.3 | System shall maintain a monthly budget with running balance calculation |
| FR-4.4 | System shall forecast days-until-out-of-cash based on daily burn rate |
| FR-4.5 | System shall parse OCR receipt text to auto-extract expense data |

### Module 5: Travel & Trip Planner
| ID | Requirement |
|---|---|
| FR-5.1 | System shall create and manage trip plans with destination, dates, and budget |
| FR-5.2 | System shall detect conflicts between trip dates and academic task deadlines |
| FR-5.3 | System shall generate AI itineraries based on destination, pace preference, and interests |
| FR-5.4 | System shall estimate trip budget breakdown by category |

### Module 6: Student Intelligence Engine
| ID | Requirement |
|---|---|
| FR-6.1 | System shall aggregate signals from all 5 domain modules into a unified student state |
| FR-6.2 | System shall compute a compound risk score (0.0–1.0) using weighted domain signals |
| FR-6.3 | System shall classify compound risk as LOW (<0.4), MEDIUM (0.4–0.69), HIGH (≥0.7) |
| FR-6.4 | System shall generate actionable insights per detected risk pattern |
| FR-6.5 | System shall recommend proactive intervention when compound risk is HIGH |

### Module 7: AI Voice Assistant & Calling System
| ID | Requirement |
|---|---|
| FR-7.1 | System shall classify user voice queries into 15+ intent categories |
| FR-7.2 | System shall execute the correct domain tool for each classified intent |
| FR-7.3 | System shall generate natural language speech responses via the LLM strategy chain |
| FR-7.4 | System shall enforce English-only output with a Hindi/Hinglish interceptor |
| FR-7.5 | System shall support 3 AI personas: Empathetic Mentor, Productivity Coach, Campus Peer |
| FR-7.6 | System shall proactively call students when deadline, sleep, or health thresholds are breached |
| FR-7.7 | System shall enforce calling policy (quiet hours, consent check, 4-hour cooldown) |
| FR-7.8 | System shall broadcast alert calls to the mobile UI via WebSocket |
| FR-7.9 | System shall persist notification state in DB to prevent duplicate alerts across restarts |

### Module 8: AI/ML Infrastructure
| ID | Requirement |
|---|---|
| FR-8.1 | System shall support a pluggable LLM strategy chain: Ollama → OpenAI → Local Engine |
| FR-8.2 | System shall cache Ollama availability status for 5 seconds to minimize health check overhead |
| FR-8.3 | System shall support hot-swapping LLM providers via environment configuration |

---

## 3. Non-Functional Requirements

### 3.1 Performance
| ID | Requirement |
|---|---|
| NFR-1.1 | Deterministic intent responses (fast-path) shall complete in < 10ms |
| NFR-1.2 | Ollama LLM responses shall target < 5s on a 10-core CPU with 8-thread inference |
| NFR-1.3 | WebSocket call broadcast shall complete in < 100ms |
| NFR-1.4 | Database reads for domain queries shall complete in < 50ms |

### 3.2 Security
| ID | Requirement |
|---|---|
| NFR-2.1 | All API credentials shall be loaded exclusively from environment variables — no hardcoded defaults |
| NFR-2.2 | Authentication tokens shall be cryptographically signed JWTs |
| NFR-2.3 | Calling consent must be verified before any proactive outbound call |

### 3.3 Reliability
| ID | Requirement |
|---|---|
| NFR-3.1 | The LLM strategy chain shall guarantee a response even when all external providers fail |
| NFR-3.2 | An observer notification failure shall not block other registered channels |
| NFR-3.3 | Sentinel alert state shall survive server restarts (DB-backed persistence) |

### 3.4 Maintainability
| ID | Requirement |
|---|---|
| NFR-4.1 | Adding a new LLM provider shall require only adding a new LLMStrategy subclass |
| NFR-4.2 | Adding a new alert channel shall require only adding a new AlertObserver subclass |
| NFR-4.3 | Adding a new voice intent shall require only adding a new IntentCommand subclass + registry entry |

### 3.5 Testability
| ID | Requirement |
|---|---|
| NFR-5.1 | Unit tests shall have zero external dependencies (no DB, network, or filesystem) |
| NFR-5.2 | CI pipeline shall enforce a minimum of 60% code coverage |
| NFR-5.3 | All parametrized test cases shall run in < 50ms each |
