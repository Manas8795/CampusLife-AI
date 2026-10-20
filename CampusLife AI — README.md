# CampusLife AI

> **An AI-powered student co-pilot for academics, health, finances, travel, and proactive personalized assistance.**

CampusLife AI is a unified student platform designed to bring multiple aspects of student life into one intelligent system.

Instead of treating academics, health, finances, and travel as isolated applications, CampusLife AI combines them under a common platform and adds an intelligence layer that can analyze information across domains, identify meaningful patterns, and provide personalized assistance.

The platform also includes an **AI Voice & Proactive Assistant**, allowing students to interact with CampusLife through natural voice conversations and enabling the system to proactively contact students when an important situation is detected.

---

## 1. Project Vision

Modern students often use separate applications for:

- Task and study management
- Health and wellness tracking
- Expense management
- Travel planning
- Reminders and notifications

This creates fragmented information.

CampusLife AI aims to provide a **single student co-pilot** that understands these different aspects of student life and uses their combined context to provide more useful assistance.

### Core idea

```text
                    CAMPUSLIFE AI
                         │
          ┌──────────────┴──────────────┐
          │                             │
    Student Modules             Intelligence Layer
          │                             │
   ┌──────┼──────┬──────┐              │
   │      │      │      │              │
 Study  Health Expense Travel ────────►│
                                        │
                              Student Intelligence
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                         Insights            Risk Detection
                              │                   │
                              └─────────┬─────────┘
                                        │
                              Proactive Intervention
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                           Web/Chat           AI Voice
```

---

# 2. Main Modules

CampusLife AI is divided into eight major modules:

1. **Platform Core & User Management**
2. **To-Do & Study Planner**
3. **Health & Wellness**
4. **Expense & Financial Manager**
5. **Travel & Vacation Planner**
6. **Student Intelligence Engine**
7. **AI Voice & Proactive Assistant**
8. **AI/ML Infrastructure, Integration & Deployment**

---

# 3. Module 1 — Platform Core & User Management

The platform foundation shared by all other modules.

### Features

- User registration
- Login/logout
- Authentication
- Session management
- Student profile
- User preferences
- Unified dashboard
- Notifications
- Quick Add
- Common API infrastructure

### Dashboard

The dashboard provides summaries from:

- To-Do
- Health
- Expenses
- Travel
- Student Intelligence
- Notifications

### Quick Add

```text
Quick Add
├── Add Task
├── Add Expense
└── Add Mood
```

---

# 4. Module 2 — To-Do & Study Planner

The academic management module.

### Features

- Create tasks
- Edit tasks
- Delete tasks
- Complete tasks
- Task prioritization
- Due dates
- Upload syllabus PDFs
- Upload study notes
- AI-generated study calendar
- Procrastination & Focus Predictor
- Task delay-risk score

### Processing Pipeline

```text
Syllabus / Notes
       │
       ▼
     GenAI
       │
       ▼
Weekly Study Calendar
       │
       ▼
     Tasks
       │
       ▼
Task Completion History
       │
       ▼
Predictive ML
       │
       ▼
Delay-Risk Score
```

### Example

A student uploads a syllabus and exam date.

CampusLife AI generates a structured weekly study plan and converts the generated plan into actionable tasks.

As the student completes tasks, the system builds completion history that can be used by the procrastination/focus model.

---

# 5. Module 3 — Health & Wellness

The student wellness module.

### Features

- Mood logging
- Sleep-hour logging
- Study-hour logging
- Energy-level tracking
- AI diet recommendations
- AI mindfulness recommendations
- Breathing/relaxation exercises
- Stress-level classification

### Stress Classification

```text
Study Hours
Sleep Hours
Exam Dates
     │
     ▼
    ML Model
     │
     ▼
┌────┼────┐
│    │    │
High Medium Low
```

### AI Wellness Generation

```text
Mood + Energy
      │
      ▼
    GenAI
      │
 ┌────┴────────────┐
 ▼                 ▼
Diet          Mindfulness
Plan          / Relaxation
```

---

# 6. Module 4 — Expense & Financial Manager

The financial management and forecasting module.

### Features

- Receipt upload
- Camera receipt capture
- OCR
- AI receipt parsing
- Expense categorization
- Merchant extraction
- Item extraction
- Amount extraction
- Expense history
- Monthly budget forecasting
- Predicted out-of-cash date

### Processing Pipeline

```text
Receipt Image
      │
      ▼
Cloud Storage
      │
      ▼
     OCR
      │
      ▼
Extracted Text
      │
      ▼
    GenAI
      │
      ▼
Structured Expense
      │
      ▼
Student Confirmation
      │
      ▼
Cloud Database
      │
      ▼
Spending History
      │
      ▼
Time-Series ML
      │
      ▼
Budget Forecast
```

This module combines **OCR + GenAI + ML**, making it one of the more technically involved components of the platform.

---

# 7. Module 5 — Travel & Vacation Planner

The travel planning module.

### Features

- Destination input
- Travel dates
- Budget
- Savings
- Academic calendar breaks
- AI-generated itinerary
- Travel cost prediction
- Lodging cost prediction
- Travel document storage
- Booking receipt storage

### Processing Pipeline

```text
Destination + Dates + Budget
             │
             ▼
           GenAI
             │
             ▼
      Day-wise Itinerary
             │
             ▼
       Travel Cost ML
             │
             ▼
       Cost Prediction
```

The travel planner can use the student's financial context to make the generated plan more appropriate to their available budget.

---

# 8. Module 6 — Student Intelligence Engine

The central intelligence layer of CampusLife AI.

The purpose of this module is to move beyond independent module-level predictions and build an understanding of the student's **overall current state**.

### Inputs

```text
Study ────────┐
Health ───────┤
Expenses ─────┼──► Student Intelligence
Travel ───────┘
```

### Responsibilities

- Student state construction
- Personal baseline calculation
- Cross-domain analysis
- Compound-risk detection
- Risk scoring
- Historical comparison
- Personalized insights
- Explainable recommendations
- Intervention decisions

### Example

The individual modules may produce:

```text
Study   → High delay risk
Health  → Poor sleep
Expense → Spending increasing
Travel  → Expensive upcoming trip
```

Student Intelligence combines these signals:

```text
Study Risk
     +
Health Signal
     +
Financial Signal
     +
Travel Context
     │
     ▼
Student Intelligence
     │
     ▼
Compound Situation
     │
     ▼
Personalized Recommendation
```

### Personal Baselines

Rather than relying only on generic thresholds, the system can compare current behavior with the student's own historical patterns.

For example:

```text
Student's normal sleep     → 7.5 hours
Recent average             → 5.8 hours
Deviation                  → -1.7 hours
```

This allows the system to reason about changes relative to the student's own history.

---

# 9. Module 7 — AI Voice & Proactive Assistant

The voice-based interaction layer of CampusLife AI.

This module allows students to interact with CampusLife using natural voice conversations and allows the platform to initiate proactive voice interactions.

### Incoming Calls

```text
Student
   │
   ▼
Phone Call
   │
   ▼
Voice System
   │
   ▼
AI Agent
   │
   ├── Tasks
   ├── Health
   ├── Expenses
   ├── Travel
   └── Student Intelligence
   │
   ▼
Response
   │
   ▼
Voice
```

### Example

Student:

> "What should I focus on tomorrow?"

The AI agent can retrieve relevant CampusLife information and respond using the student's current context.

### Proactive Calls

Student Intelligence can identify situations where proactive intervention is appropriate.

```text
Student Intelligence
        │
        ▼
Important Situation
Detected
        │
        ▼
Intervention Engine
        │
        ▼
AI Voice Agent
        │
        ▼
Phone Call
        │
        ▼
Student
```

Example:

> "Your exam is in two days and several high-priority tasks are still incomplete. Your recent sleep is also below your usual level. Would you like me to help create a plan for tomorrow?"

The voice system therefore acts as an **interaction mechanism for CampusLife Intelligence**, rather than being an isolated calling feature.

---

# 10. Module 8 — AI/ML Infrastructure, Integration & Deployment

The shared technical infrastructure supporting the entire platform.

### AI Infrastructure

- Shared LLM client
- GenAI API integration
- Prompt management
- Structured AI outputs
- Tool/function calling
- AI response validation

### ML Infrastructure

Hosts and serves the project's models:

- Procrastination & Focus Predictor
- Stress Level Classifier
- Budget Forecast Model
- Travel Cost Estimator
- Student-risk models

### OCR

Used primarily for receipt processing.

```text
Receipt
   │
   ▼
 OCR
   │
   ▼
Text
   │
   ▼
GenAI Parser
```

### Memory / RAG

The system can maintain historical student information and retrieve relevant past context when generating personalized insights.

```text
Student History
      │
      ▼
Semantic Memory
      │
      ▼
Relevant Past Context
      │
      ▼
AI / Student Intelligence
```

### Backend

```text
                    API Gateway
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    todo_service   health_service   expense_service
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  travel_service
                         │
                         ▼
             Student Intelligence
                         │
                         ▼
                    Voice Agent
```

---

# 11. Overall Architecture

```text
                           CAMPUSLIFE AI
                                │
                                ▼
                       ┌─────────────────┐
                       │   FRONTEND UI   │
                       │ React / Next.js │
                       └────────┬────────┘
                                │
                            REST / API
                                │
                                ▼
                       ┌─────────────────┐
                       │   API GATEWAY   │
                       └────────┬────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
       Todo Service       Health Service      Expense Service
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                                ▼
                        Travel Service
                                │
                                ▼
                 ┌──────────────────────────┐
                 │  Student Intelligence    │
                 │                          │
                 │ State + Baselines        │
                 │ Cross-domain Analysis    │
                 │ Risk Detection           │
                 │ Memory / RAG              │
                 │ Explainability           │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Proactive Intervention   │
                 └────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                 Web/Chat           AI Voice
                                      │
                                    Twilio
                                      │
                                      ▼
                                   Phone
```

---

# 12. AI/ML Distribution

| Module | AI/ML Component |
|---|---|
| To-Do & Study | AI Study Calendar |
| To-Do & Study | Procrastination & Focus Predictor |
| Health | AI Diet Planner |
| Health | AI Mindfulness Generator |
| Health | Stress Classifier |
| Expense | OCR |
| Expense | AI Receipt Parser |
| Expense | Budget Forecasting |
| Travel | AI Itinerary Generator |
| Travel | Travel Cost Estimator |
| Student Intelligence | Cross-domain risk detection |
| Student Intelligence | Personal baseline analysis |
| Student Intelligence | Personalized recommendations |
| Student Intelligence | Historical memory/RAG |
| AI Voice | Conversational AI Agent |
| AI Voice | CampusLife tool calling |
| AI Voice | Proactive voice intervention |

---

# 13. Data Architecture

### Main Entities

```text
USER
 │
 ├── TASKS
 │     └── Study Plans
 │     └── Delay Risk
 │
 ├── HEALTH LOGS
 │     └── Mood
 │     └── Sleep
 │     └── Study Hours
 │     └── Stress
 │
 ├── EXPENSES
 │     └── Merchant
 │     └── Items
 │     └── Amount
 │     └── Category
 │
 ├── ITINERARIES
 │     └── Destination
 │     └── Dates
 │     └── Cost
 │
 └── STUDENT INTELLIGENCE
       ├── Personal Baselines
       ├── Risk Scores
       ├── Insights
       ├── Interventions
       └── Historical Context
```

### Cloud Storage

Stores:

- Syllabus PDFs
- Study notes
- Receipt images
- Travel documents
- Booking receipts

---

# 14. Suggested Technology Stack

### Frontend

- React.js / Next.js
- Responsive UI
- REST/JSON communication

### Backend

- FastAPI
- Python
- REST APIs

### Database

- PostgreSQL

### Storage

One of:

- Supabase Storage
- AWS S3
- Firebase Storage

### Authentication

One of:

- Firebase Auth
- NextAuth.js

### AI

- LLM API
- Structured outputs
- Function/tool calling
- RAG / semantic retrieval

### Machine Learning

- Python
- Scikit-learn
- Time-series models where appropriate
- Model serving through backend services

### OCR

- OCR service/library for receipt text extraction

### Voice

- Twilio Voice
- Speech/voice processing
- LLM-based conversational agent
- CampusLife API tool calling

### DevOps

- GitHub
- GitHub Actions
- CI/CD
- Cloud deployment

---

# 15. Development Structure

The project can be developed incrementally.

```text
Phase 1
Platform Core
       ↓
Phase 2
To-Do & Study
       ↓
Phase 3
Health
       ↓
Phase 4
Expense
       ↓
Phase 5
Travel
       ↓
Phase 6
Student Intelligence
       ↓
Phase 7
AI Voice & Proactive Assistant
       ↓
Phase 8
Integration + Testing + Deployment
```

The original project distribution separates the core platform from the four feature branches and the shared AI/backend/cloud infrastructure. The expanded architecture introduces Student Intelligence and AI Voice as additional major modules on top of that foundation.

---

# 16. Project Goals

CampusLife AI aims to provide:

- One unified student platform
- AI-assisted academic planning
- Personalized wellness support
- Automated expense management
- Budget-aware travel planning
- Predictive student analytics
- Cross-domain student intelligence
- Personalized historical context
- Explainable recommendations
- Proactive interventions
- Natural voice interaction
- AI-powered phone assistance

---

# 17. Example End-to-End Scenario

A student has an exam in three days.

CampusLife detects:

```text
Exam → 3 days away
        │
        ├── 5 unfinished tasks
        ├── High delay-risk
        ├── Sleep below personal baseline
        └── Study hours declining
                │
                ▼
       Student Intelligence
                │
                ▼
       High compound-risk state
                │
                ▼
      Proactive Intervention
                │
                ▼
          AI Voice Agent
                │
                ▼
           Phone Call
```

The student can then speak naturally with the system and ask it to:

- Explain the situation
- Create a study plan
- Prioritize tasks
- Check available time
- Modify tasks
- Provide a relaxation activity

This connects the platform's **data, prediction, intelligence, and interaction layers into one workflow**.

---

# 18. Project Structure

A possible repository structure:

```text
campuslife-ai/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── dashboard/
│   ├── study/
│   ├── health/
│   ├── expense/
│   ├── travel/
│   ├── intelligence/
│   └── voice/
│
├── backend/
│   ├── api/
│   ├── services/
│   │   ├── todo_service/
│   │   ├── health_service/
│   │   ├── expense_service/
│   │   ├── travel_service/
│   │   ├── intelligence_service/
│   │   └── voice_service/
│   │
│   ├── models/
│   ├── schemas/
│   ├── database/
│   ├── auth/
│   └── main.py
│
├── ai/
│   ├── genai/
│   ├── rag/
│   ├── prompts/
│   └── tools/
│
├── ml/
│   ├── procrastination/
│   ├── stress/
│   ├── budget/
│   ├── travel/
│   └── student_risk/
│
├── ocr/
│
├── voice/
│   ├── twilio/
│   ├── agent/
│   └── tools/
│
├── tests/
│
├── docs/
│
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 19. Development Philosophy

CampusLife AI is designed as a **loosely coupled modular platform**.

Each feature module should remain independently functional while exposing APIs that allow the Student Intelligence layer to consume relevant information.

The goal is:

```text
Independent Modules
        ↓
Shared APIs
        ↓
Student Intelligence
        ↓
Personalized Decisions
        ↓
Proactive Interaction
```

This keeps the system modular while allowing the different aspects of student life to contribute to a unified student context.

---

# 20. Project Summary

**CampusLife AI** is a unified student co-pilot that combines:

```text
Academic Management
        +
Health & Wellness
        +
Financial Management
        +
Travel Planning
        +
Machine Learning
        +
Generative AI
        +
Student Intelligence
        +
AI Voice Interaction
```

The four primary student modules provide the underlying data and functionality.

The **Student Intelligence Engine** connects those domains and develops a broader understanding of the student's current situation.

The **AI Voice & Proactive Assistant** turns that intelligence into a natural interaction mechanism capable of both responding to students and proactively reaching out when appropriate.

The result is a single platform designed not merely to record student activities, but to **understand context, identify meaningful situations, and assist the student proactively.**