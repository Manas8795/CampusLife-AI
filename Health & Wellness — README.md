# CampusLife AI — Health & Wellness

## 1. Overview

The **Health & Wellness** module is responsible for helping students monitor and improve their day-to-day physical and mental wellness.

The module combines:

- Mood tracking
- Sleep tracking
- Study-hour tracking
- Energy-level tracking
- Stress classification
- AI-generated wellness recommendations
- AI diet recommendations
- AI mindfulness and relaxation guidance
- Health-related signals for the Student Intelligence Engine

The module is designed as a **wellness support system**, not a medical diagnosis or treatment system.

---

# 2. Module Responsibilities

```text
Health & Wellness
│
├── Mood Tracking
├── Sleep Tracking
├── Study-Hour Tracking
├── Energy Tracking
├── Stress Classification
├── AI Wellness Recommendations
├── AI Diet Recommendations
├── AI Mindfulness / Relaxation
└── Student Intelligence Integration
```

The module owns health and wellness-related student data and processing.

It does **not** own:

- Authentication
- User identity
- General notifications infrastructure
- Academic task management
- Expense management
- Travel planning
- Cross-domain student intelligence

Those responsibilities belong to other CampusLife modules.

---

# 3. Core Features

### Wellness Tracking

Students can record:

- Mood
- Sleep duration
- Study duration
- Energy level
- Optional wellness notes

### AI Features

The module can provide:

- Personalized wellness suggestions
- Diet recommendations
- Mindfulness recommendations
- Relaxation/breathing exercises

### Machine Learning

The module includes a stress classification component that can use historical student information to estimate a student's current stress level.

---

# 4. Wellness Data

A wellness record represents the student's state at a particular point in time.

A record may contain:

```text id="wq2b7m"
Wellness Record
│
├── ID
├── User ID
├── Date
├── Mood
├── Sleep Hours
├── Study Hours
├── Energy Level
├── Stress Level
└── Notes
```

The exact fields can be adjusted during implementation.

---

# 5. Mood Tracking

Students should be able to record their current mood.

A simple initial scale can be:

```text id="k3h1qd"
Mood
│
├── Very Low
├── Low
├── Neutral
├── Good
└── Very Good
```

The application can optionally allow the student to add a short note explaining the mood.

Example:

```text id="v5m2rq"
Mood: Low
Note: "Too much academic workload today."
```

Mood history becomes useful for identifying changes in the student's personal baseline.

---

# 6. Sleep Tracking

Students can record their sleep duration.

Example:

```text id="q7f4sx"
Date       Sleep
------------------
Monday     7.5 h
Tuesday    6.8 h
Wednesday  5.5 h
Thursday   5.9 h
```

The system can calculate:

- Daily sleep
- Weekly average
- Recent sleep trend
- Deviation from personal baseline

Example:

```text id="d6q9pl"
Personal Average Sleep → 7.4 h
Recent Average         → 5.8 h
Deviation              → -1.6 h
```

This information can be consumed by the Student Intelligence Engine.

---

# 7. Study-Hour Tracking

The module can store the number of hours a student spends studying.

```text id="f3r7kp"
Daily Study Hours
       │
       ▼
Historical Records
       │
       ▼
Trend Analysis
```

Study-hour data can also be shared with the To-Do & Study Planner and Student Intelligence Engine.

This creates a connection between academic workload and wellness.

---

# 8. Energy-Level Tracking

Students can record their perceived energy level.

For example:

```text id="m8w4zt"
Energy
│
├── Very Low
├── Low
├── Moderate
├── High
└── Very High
```

Energy can be used together with mood, sleep, and study behavior to build a broader wellness picture.

---

# 9. Wellness Logging Flow

```text id="n4p8yd"
Student
   │
   ▼
Log Wellness Data
   │
   ├── Mood
   ├── Sleep
   ├── Study Hours
   └── Energy
   │
   ▼
Validation
   │
   ▼
PostgreSQL
   │
   ▼
Wellness History
```

The stored history can later be used for AI and ML processing.

---

# 10. Stress Classification

The module contains an ML component for estimating stress level.

A basic classification scheme is:

```text id="x7j2na"
Stress Level
│
├── LOW
├── MEDIUM
└── HIGH
```

### Possible Inputs

The model can use signals such as:

- Sleep duration
- Study hours
- Mood
- Energy level
- Upcoming academic deadlines
- Historical wellness behavior

The exact feature set should be finalized during model development and validation.

---

# 11. Stress Prediction Pipeline

```text id="c5n8zr"
Wellness Data
     │
     ├── Sleep
     ├── Mood
     ├── Energy
     └── Study Hours
     │
     ▼
Feature Engineering
     │
     ▼
Stress ML Model
     │
     ▼
Stress Classification
     │
 ┌───┼────┐
 ▼   ▼    ▼
Low Medium High
```

The model should return a structured prediction.

Example:

```json id="q2v9ls"
{
  "stress_level": "HIGH",
  "confidence": 0.84
}
```

The exact output structure depends on the selected model.

---

# 12. Personal Baseline

The Health & Wellness module should support comparison against the student's own historical behavior.

Instead of relying only on universal thresholds, the system can identify meaningful changes relative to the student's normal behavior.

Example:

```text id="u6m3kx"
Normal Sleep      → 7.5 hours
Recent Sleep      → 5.7 hours
                   ↓
Significant change
```

Similarly:

```text id="p4y8cw"
Normal Mood       → Good
Recent Mood       → Low
Normal Study      → 3.5 h/day
Recent Study      → 6.0 h/day
                   ↓
Potential overload signal
```

These signals can be passed to Student Intelligence.

---

# 13. AI Wellness Recommendations

The module can use GenAI to provide personalized wellness suggestions.

### Inputs

```text id="r3v7hd"
Mood
Sleep
Energy
Study Hours
Stress Level
      │
      ▼
     GenAI
      │
      ▼
Wellness Recommendation
```

The recommendation should be based on the student's recorded context.

Example categories:

- Rest recommendation
- Study-break recommendation
- Relaxation activity
- Sleep-hygiene suggestion
- General wellness activity

---

# 14. AI Diet Recommendations

The module can provide general diet suggestions based on the student's provided context.

Possible inputs:

- Current energy level
- Activity/study load
- General dietary preferences
- Meal timing
- Wellness context

```text id="j8x5qd"
Student Context
      │
      ▼
     GenAI
      │
      ▼
General Diet Suggestions
```

The system should clearly distinguish general wellness suggestions from professional medical or nutritional advice.

---

# 15. AI Mindfulness & Relaxation

The module can generate short wellness activities such as:

- Breathing exercises
- Short relaxation sessions
- Mindfulness prompts
- Study-break activities

### Example Flow

```text id="b9s2mk"
High Stress
    │
    ▼
Wellness Module
    │
    ▼
GenAI
    │
    ▼
Short Relaxation Exercise
```

These activities should be designed for general wellness rather than treatment of a medical or psychiatric condition.

---

# 16. Student Intelligence Integration

Health is one of the primary data sources for the Student Intelligence Engine.

```text id="z7c4px"
                HEALTH MODULE
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
     Mood          Sleep         Energy
       │             │             │
       └─────────────┼─────────────┘
                     ▼
               Stress Signal
                     │
                     ▼
           Student Intelligence
```

The Intelligence Engine can combine health information with academic and other CampusLife signals.

### Example

```text id="m6t2vn"
Upcoming Exam
      +
High Task Delay
      +
Poor Sleep
      +
Low Energy
      ↓
Student Intelligence
      ↓
Potential Academic-Wellness Risk
```

The Health module supplies the health signals; the Student Intelligence Engine performs the cross-domain reasoning.

---

# 17. Notifications Integration

The Health module can generate events for the shared notification service.

Examples:

- Wellness logging reminder
- Important wellness trend
- Stress status change
- Suggested wellness activity

```text id="n5k8rz"
Health Module
     │
     ▼
Wellness Event
     │
     ▼
Notification Service
     │
     ▼
Student
```

The notification infrastructure remains owned by Platform Core.

---

# 18. API Design

A possible initial API structure:

### Wellness Logs

```text id="y3p7mc"
POST   /health/logs
GET    /health/logs
GET    /health/logs/{id}
PATCH  /health/logs/{id}
DELETE /health/logs/{id}
```

### Wellness Summary

```text id="r8k4zd"
GET    /health/summary
GET    /health/trends
```

### Stress Prediction

```text id="w2n6qx"
GET    /health/stress
POST   /health/stress/predict
```

### AI Recommendations

```text id="s7v3kp"
POST   /health/recommendations
POST   /health/diet
POST   /health/mindfulness
```

These endpoints are an initial design and may change during implementation.

---

# 19. Suggested Data Model

```text id="e4y9rc"
USER
 │
 └── HEALTH_RECORD
       │
       ├── id
       ├── user_id
       ├── date
       ├── mood
       ├── sleep_hours
       ├── study_hours
       ├── energy_level
       ├── stress_level
       ├── stress_score
       ├── notes
       └── created_at
```

For better normalization, stress predictions and AI recommendations can also be stored in separate tables.

For example:

```text id="p8m2vd"
health_records
stress_predictions
wellness_recommendations
```

---

# 20. Suggested Backend Structure

```text id="t7q4xn"
backend/
│
├── app/
│   └── health/
│       ├── router.py
│       ├── service.py
│       ├── schemas.py
│       ├── models.py
│       └── dependencies.py
│
├── ai/
│   ├── wellness.py
│   ├── diet.py
│   ├── mindfulness.py
│   └── prompts/
│
├── ml/
│   └── stress/
│       ├── model.py
│       ├── features.py
│       ├── predictor.py
│       └── preprocessing.py
│
└── tests/
    ├── test_health.py
    ├── test_stress.py
    └── test_recommendations.py
```

The final structure should follow the overall CampusLife repository architecture.

---

# 21. AI Architecture

AI-generated wellness content should be separated from the core health-record system.

```text id="c9r5yk"
Health API
    │
    ▼
Health Service
    │
    ├───────────────┐
    ▼               ▼
Health Data       AI Service
    │               │
    │          ┌────┼────┐
    │          ▼    ▼    ▼
    │        Diet Mindfulness
    │
    └───────────────┐
                    ▼
              Recommendation
```

The backend should validate AI-generated outputs before returning them to the frontend.

---

# 22. ML Architecture

The stress model should remain independent from the GenAI recommendation system.

```text id="h5v8qs"
Health History
     │
     ▼
Feature Engineering
     │
     ▼
Stress Model
     │
     ▼
Stress Prediction
     │
     ├──────────────┐
     ▼              ▼
Health UI      Student Intelligence
```

The LLM can use the resulting stress classification as context for generating a general wellness recommendation.

---

# 23. Explainability

Stress predictions should provide interpretable information where possible.

Example:

```json id="m9c3zt"
{
  "stress_level": "HIGH",
  "confidence": 0.84,
  "signals": [
    "LOW_SLEEP",
    "HIGH_STUDY_HOURS",
    "LOW_ENERGY"
  ]
}
```

The system should distinguish between:

- Model-derived signals
- User-provided information
- AI-generated recommendations

This helps prevent the AI layer from presenting generated text as a clinical assessment.

---

# 24. Privacy & Security

Health and wellness information is personal data and must receive appropriate protection.

Requirements:

- Authenticate all health endpoints
- Enforce user-level authorization
- Prevent cross-user access
- Encrypt data in transit
- Protect database credentials
- Avoid exposing sensitive health data in logs
- Restrict access to wellness records
- Store secrets in environment variables or secure secret storage

The system should collect only information necessary for the features being implemented.

---

# 25. Health Data Boundaries

The module is intended for **general student wellness support**.

It should not claim to:

- Diagnose diseases
- Diagnose mental-health disorders
- Replace a doctor
- Replace a qualified dietitian
- Provide emergency medical care
- Make definitive medical conclusions

When a situation appears to require professional support, the application should direct the student toward an appropriate qualified professional or emergency service rather than attempting to provide medical treatment.

---

# 26. Testing

### Wellness Record Tests

- Create wellness record
- Retrieve records
- Update record
- Delete record
- Date validation
- Input validation

### Stress Model Tests

- Feature generation
- Prediction
- Classification
- Missing-data handling
- Model loading

### AI Tests

- Wellness recommendation generation
- Diet recommendation generation
- Mindfulness generation
- Structured-output validation
- Invalid AI response handling

### Authorization Tests

- User can access own health records
- User cannot access another user's records
- Protected endpoints reject unauthenticated requests

---

# 27. Definition of Done

The Health & Wellness module is considered complete when:

- [ ] Students can log mood
- [ ] Students can log sleep
- [ ] Students can log study hours
- [ ] Students can log energy level
- [ ] Wellness history is stored
- [ ] Wellness trends can be displayed
- [ ] Stress classification works
- [ ] Stress predictions provide interpretable signals
- [ ] AI wellness recommendations work
- [ ] AI diet recommendations work
- [ ] AI mindfulness recommendations work
- [ ] Health signals can be consumed by Student Intelligence
- [ ] Notifications can be generated
- [ ] User-level authorization is enforced
- [ ] Sensitive information is protected
- [ ] Automated tests are implemented

---

# 28. Role in CampusLife AI

The Health & Wellness module provides the **wellness context** required by the larger CampusLife system.

```text id="x6n2wb"
                 HEALTH & WELLNESS
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      Mood             Sleep            Energy
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 Stress Classification
                         │
                         ▼
                Student Intelligence
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Cross-Domain              Personalized
          Analysis                Insights
             │                       │
             └───────────┬───────────┘
                         ▼
                  Proactive Assistant
                         │
                         ▼
                     AI Voice
```

The module therefore has two primary roles:

1. **Provide students with practical wellness tracking and AI-assisted wellness support.**
2. **Provide reliable health-related signals to the Student Intelligence Engine.**

The Health & Wellness module remains independently usable while contributing an important dimension to CampusLife AI's broader understanding of the student's overall state.