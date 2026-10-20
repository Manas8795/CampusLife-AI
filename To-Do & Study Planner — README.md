# CampusLife AI — To-Do & Study Planner

## 1. Overview

The **To-Do & Study Planner** is the academic productivity module of CampusLife AI.

It combines conventional task management with AI-assisted study planning and machine-learning-based productivity analysis.

The module allows students to:

- Create and manage tasks
- Organize academic work
- Upload syllabus and study material
- Generate personalized study schedules
- Track task completion
- Estimate procrastination and focus risk
- Provide academic insights to the Student Intelligence Engine

---

# 2. Module Responsibilities

```text id="8cv5v9"
To-Do & Study Planner
│
├── Task Management
├── Academic Material Management
├── AI Study Planning
├── Task Prioritization
├── Progress Tracking
├── Procrastination & Focus Prediction
└── Student Intelligence Integration
```

The module owns academic task and study-planning logic.

It does **not** own authentication, user identity, notifications infrastructure, or the overall Student Intelligence Engine.

---

# 3. Core Features

### Task Management

- Create tasks
- Edit tasks
- Delete tasks
- Mark tasks as completed
- Set due dates
- Set priorities
- Add descriptions
- Organize tasks by academic context
- Track completion history

### Study Planning

- Upload syllabus
- Upload study notes
- Provide examination dates
- Generate AI study schedules
- Break large academic goals into smaller tasks
- Track planned versus completed work

### Productivity Prediction

- Analyze task completion behavior
- Identify possible procrastination patterns
- Estimate focus/delay risk
- Provide risk information to Student Intelligence

---

# 4. Task Management

The task manager is the foundation of the module.

### Task Lifecycle

```text id="qq8cwl"
Create Task
    │
    ▼
Pending
    │
    ├───────────────┐
    │               │
    ▼               ▼
In Progress      Overdue
    │               │
    └───────┬───────┘
            ▼
        Completed
```

A task should maintain enough historical information to allow the system to understand the student's completion behavior.

---

# 5. Task Data

A task can contain information such as:

```text id="4awh3h"
Task
├── ID
├── User ID
├── Title
├── Description
├── Subject / Category
├── Priority
├── Status
├── Created At
├── Due Date
├── Completed At
└── Source
```

`Source` can distinguish between tasks created manually and tasks generated from an AI study plan.

---

# 6. Task Priority

Tasks should support priority levels.

For example:

```text id="o5p5y7"
Priority
│
├── Low
├── Medium
└── High
```

Priority can be used by the study planner when determining which tasks should receive attention first.

---

# 7. Task Status

Recommended statuses:

```text id="a0bd6y"
PENDING
IN_PROGRESS
COMPLETED
OVERDUE
```

The exact state model can be adjusted during implementation.

---

# 8. Academic Material

The module can accept academic material such as:

- Syllabus documents
- Study notes
- Course material

### Upload Flow

```text id="pknf3q"
Student
   │
   ▼
Upload Syllabus / Notes
   │
   ▼
Cloud Storage
   │
   ▼
Document Processing
   │
   ▼
AI Study Planner
```

The actual file-storage implementation belongs to the shared infrastructure, while the Study Planner determines how the academic material is used.

---

# 9. AI Study Planner

The AI Study Planner generates a structured study schedule based on available academic information.

### Inputs

Potential inputs include:

- Syllabus
- Study material
- Examination date
- Available study time
- Existing tasks
- Task priorities
- Existing schedule

### Processing

```text id="7f8x1r"
Syllabus
   +
Exam Date
   +
Available Time
   +
Existing Tasks
   │
   ▼
   GenAI
   │
   ▼
Study Plan
   │
   ▼
Daily / Weekly Tasks
```

The generated plan should be converted into structured data rather than remaining only as natural-language text.

---

# 10. AI Study Plan Output

A generated plan can conceptually contain:

```text id="n7m9pf"
Study Plan
│
├── Date
├── Subject
├── Topic
├── Task
├── Estimated Duration
├── Priority
└── Recommended Order
```

Example:

```text id="p7s1wk"
Monday
├── DBMS — Normalization — 60 min
├── OS — Scheduling — 45 min
└── DSA — Graph Revision — 60 min

Tuesday
├── DBMS — Transactions — 60 min
└── DSA — BFS / DFS — 90 min
```

The exact generated schedule should depend on the student's provided academic context.

---

# 11. Task Generation From Study Plans

The AI planner should be able to transform a study plan into actionable tasks.

```text id="m3w5zi"
AI Study Plan
     │
     ▼
Structured Plan
     │
     ▼
Task Generator
     │
     ├── Task 1
     ├── Task 2
     ├── Task 3
     └── ...
     │
     ▼
Task Database
```

The student should be able to review and modify generated tasks before or after adding them to their task list.

---

# 12. Progress Tracking

The module should track academic progress using task history.

Possible metrics include:

- Tasks created
- Tasks completed
- Tasks pending
- Tasks overdue
- Completion percentage
- Completion rate over time
- Planned versus completed tasks

### Example

```text id="31m57v"
Weekly Tasks

Completed     ███████████████
In Progress   █████
Pending       ████
Overdue       ██
```

These metrics become useful inputs for the productivity prediction component and Student Intelligence Engine.

---

# 13. Procrastination & Focus Predictor

The module includes an ML component designed to identify potential procrastination or focus-related risk.

### Inputs

Potential features include:

- Task completion history
- Number of overdue tasks
- Task delay
- Completion rate
- Task priority
- Due-date proximity
- Historical productivity

### Pipeline

```text id="y7zqvw"
Task History
     │
     ▼
Feature Engineering
     │
     ▼
ML Model
     │
     ▼
Delay / Focus Risk
```

---

# 14. Risk Output

The model should produce a structured result rather than an unstructured statement.

For example:

```json id="kq8b2v"
{
  "risk_level": "HIGH",
  "risk_score": 0.81,
  "reason_codes": [
    "HIGH_PENDING_TASK_COUNT",
    "RECENT_TASK_DELAYS",
    "UPCOMING_DEADLINES"
  ]
}
```

The exact model output and score range should be defined during implementation.

---

# 15. Explainability

The system should provide understandable reasons for a productivity-risk prediction.

Instead of:

> "Your procrastination risk is 81%."

the application should provide information such as:

> "Your risk is elevated because several high-priority tasks are approaching their deadlines and your recent completion rate has decreased."

The explanation should be based on actual model inputs or predefined reason codes rather than invented explanations.

---

# 16. Integration With Student Intelligence

The Study Planner is one of the primary data sources for the Student Intelligence Engine.

```text id="0p5bqu"
              STUDY MODULE
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Tasks     Progress    Risk Score
        │          │          │
        └──────────┼──────────┘
                   ▼
         Student Intelligence
```

Student Intelligence can combine academic signals with:

- Health
- Expenses
- Travel
- Personal baselines

For example:

```text id="4m0qjs"
Upcoming Exam
      +
High Task Delay
      +
Low Completion Rate
      +
Poor Sleep
      ↓
Student Intelligence
      ↓
Compound Student Risk
```

The Study module itself should not make this cross-domain decision.

---

# 17. Notifications Integration

The module can generate events for the shared Notification Service.

Examples:

- Task deadline approaching
- Task overdue
- Study plan generated
- Study plan changed
- Important academic milestone

```text id="0n84kz"
Study Module
     │
     ▼
Academic Event
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

### Tasks

```text id="8vl2gp"
POST   /tasks
GET    /tasks
GET    /tasks/{id}
PATCH  /tasks/{id}
DELETE /tasks/{id}
POST   /tasks/{id}/complete
```

### Study Material

```text id="7xw8eg"
POST   /study-material
GET    /study-material
GET    /study-material/{id}
DELETE /study-material/{id}
```

### Study Plans

```text id="y7c6hn"
POST   /study-plans/generate
GET    /study-plans
GET    /study-plans/{id}
PATCH  /study-plans/{id}
DELETE /study-plans/{id}
```

### Productivity Prediction

```text id="p3a2vx"
GET    /productivity/risk
GET    /productivity/history
```

These endpoints represent an initial design and can be modified during implementation.

---

# 19. Suggested Data Model

```text id="i7r4iz"
USER
 │
 ├── TASK
 │    ├── title
 │    ├── description
 │    ├── priority
 │    ├── status
 │    ├── due_date
 │    ├── created_at
 │    └── completed_at
 │
 ├── STUDY_MATERIAL
 │    ├── file
 │    ├── type
 │    └── metadata
 │
 ├── STUDY_PLAN
 │    ├── exam_date
 │    ├── start_date
 │    ├── end_date
 │    └── generated_at
 │
 └── PRODUCTIVITY_RECORD
      ├── risk_score
      ├── risk_level
      ├── features
      └── created_at
```

A normalized relational implementation should be used in PostgreSQL.

---

# 20. Suggested Backend Structure

```text id="e7g3jx"
backend/
│
├── app/
│   ├── study/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   └── dependencies.py
│   │
│   ├── tasks/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py
│   │
│   └── productivity/
│       ├── router.py
│       ├── service.py
│       └── schemas.py
│
├── ai/
│   ├── study_planner.py
│   └── prompts/
│
├── ml/
│   └── procrastination/
│       ├── model.py
│       ├── features.py
│       └── predictor.py
│
└── tests/
    ├── test_tasks.py
    ├── test_study_plans.py
    └── test_productivity.py
```

The final directory structure should follow the overall CampusLife repository architecture.

---

# 21. AI Architecture

The AI Study Planner should be separated from ordinary task CRUD operations.

```text id="kz7x2a"
             Study Planner API
                    │
                    ▼
              Study Service
                    │
                    ▼
             AI Planner Service
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Syllabus     Exam Date    Availability
       │            │            │
       └────────────┼────────────┘
                    ▼
                   LLM
                    │
                    ▼
          Structured Study Plan
                    │
                    ▼
              Task Generator
```

The AI layer should return structured information that can be validated by the backend before being stored.

---

# 22. ML Architecture

The productivity model should be independent from the LLM.

```text id="q8y3l7"
Task Database
     │
     ▼
Historical Records
     │
     ▼
Feature Engineering
     │
     ▼
ML Model
     │
     ▼
Risk Prediction
     │
     ▼
Study Module
     │
     ▼
Student Intelligence
```

The LLM should not be responsible for generating the numerical prediction.

---

# 23. Security & Authorization

All task and study data must be associated with the authenticated user.

A user must only be able to:

- View their own tasks
- Modify their own tasks
- Delete their own tasks
- View their own study plans
- Access their own uploaded study material
- Access their own productivity history

Every protected endpoint should derive the user identity from the authentication system rather than accepting an arbitrary user ID from the client.

---

# 24. Validation

The backend should validate:

- Task title
- Task status
- Priority
- Dates
- Study-plan dates
- Exam dates
- Uploaded file types
- File size
- AI-generated structured output

Invalid input should produce consistent API validation errors.

---

# 25. Testing

### Task Tests

- Create task
- Retrieve tasks
- Update task
- Delete task
- Complete task
- Due-date handling
- Priority handling

### Study Planner Tests

- Study material upload
- Study plan generation
- Study plan validation
- Task generation from study plan

### ML Tests

- Feature generation
- Prediction
- Risk classification
- Invalid/missing input handling

### Authorization Tests

- User cannot access another user's tasks
- User cannot access another user's study material
- User cannot modify another user's study plan

---

# 26. Definition of Done

The To-Do & Study Planner is considered complete when:

- [ ] Tasks can be created
- [ ] Tasks can be edited
- [ ] Tasks can be deleted
- [ ] Tasks can be completed
- [ ] Task priorities work
- [ ] Due dates work
- [ ] Study material can be uploaded
- [ ] AI study plans can be generated
- [ ] Generated plans can be converted into tasks
- [ ] Study progress is tracked
- [ ] Productivity history is stored
- [ ] Procrastination/focus prediction works
- [ ] Predictions have understandable reason codes
- [ ] Student Intelligence can consume academic signals
- [ ] Notifications can be generated
- [ ] User-level authorization is enforced
- [ ] Automated tests are implemented

---

# 27. Role in CampusLife AI

The To-Do & Study Planner provides the **academic context** required by the broader CampusLife system.

```text id="trqv6w"
                 TO-DO & STUDY
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Tasks        Study Plan     Productivity
                                      Risk
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Student Intelligence
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Personalized         Proactive
         Insight            Intervention
                                 │
                                 ▼
                            AI Voice
```

The module therefore has two distinct roles:

1. **Provide students with practical academic planning and task-management tools.**
2. **Provide reliable academic signals to the Student Intelligence Engine.**

The module remains independently usable while contributing academic context to the larger CampusLife AI ecosystem.