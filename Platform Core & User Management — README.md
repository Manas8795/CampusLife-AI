# CampusLife AI — Platform Core & User Management

## 1. Overview

The **Platform Core & User Management** module is the foundational layer of CampusLife AI.

It provides the common services required by every other CampusLife module, including:

- User registration and authentication
- Student profiles
- Session management
- User preferences
- Unified dashboard
- Notifications
- Quick Add
- Shared API infrastructure
- Common security and validation

The module does **not** contain the domain-specific logic for Study, Health, Expense, Travel, or Student Intelligence. Instead, it provides the common platform services that allow those modules to operate consistently.

---

# 2. Responsibilities

The module is responsible for five major areas:

```text
Platform Core
│
├── Authentication
├── User Management
├── Dashboard
├── Notifications
└── Shared Platform Services
```

---

# 3. Authentication

Authentication controls access to CampusLife AI.

### Features

- User registration
- Login
- Logout
- Session/token management
- Password management
- Authentication state
- Protected API endpoints

### Authentication Flow

```text
User
 │
 ▼
Register / Login
 │
 ▼
Authentication Service
 │
 ├── Validate credentials
 │
 └── Create authenticated session
 │
 ▼
Authenticated User
 │
 ▼
CampusLife Dashboard
```

### Protected Resources

Only authenticated users should be able to access personal:

- Tasks
- Health records
- Expenses
- Travel plans
- Student intelligence
- AI interactions

---

# 4. User Management

Each CampusLife account represents a student.

### User Profile

The profile stores information required by the platform and personalization systems.

Possible profile information includes:

- Name
- Email
- Profile image
- Academic information
- Preferences
- Time zone
- Notification preferences
- AI interaction preferences

The profile should provide information required by other CampusLife modules without duplicating user data across individual services.

---

# 5. User Preferences

CampusLife should maintain centralized preferences.

Examples:

```text
User Preferences
│
├── Notification preferences
├── Study preferences
├── AI preferences
├── Voice preferences
├── Display preferences
└── Privacy preferences
```

Other modules can consume these preferences through the platform's common API layer.

---

# 6. Unified Dashboard

The dashboard acts as the central entry point to CampusLife AI.

It should provide a high-level summary rather than duplicate the complete functionality of each module.

### Dashboard Sections

```text
                    DASHBOARD
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
      Study           Health          Expenses
        │               │                │
        └───────────────┼────────────────┘
                        │
                        ▼
                      Travel
                        │
                        ▼
               Student Intelligence
                        │
                        ▼
                  Notifications
```

### Example Dashboard Information

**Study**
- Today's pending tasks
- Upcoming deadlines
- Study progress

**Health**
- Recent mood
- Sleep summary
- Wellness status

**Expenses**
- Current spending
- Monthly budget status

**Travel**
- Upcoming trips
- Planned travel expenses

**Student Intelligence**
- Current student-state summary
- Important insights
- Recommended actions

---

# 7. Notification System

The notification service provides a common mechanism for communicating important events to the student.

### Notification Sources

Notifications may originate from:

- Study Planner
- Health & Wellness
- Expense Manager
- Travel Planner
- Student Intelligence
- System events

### Notification Flow

```text
Module
  │
  ▼
Event Generated
  │
  ▼
Notification Service
  │
  ├── Check user preferences
  ├── Determine priority
  └── Create notification
  │
  ▼
Student
```

### Notification Types

Examples:

- Task deadline approaching
- Study plan update
- Important wellness insight
- Budget warning
- Upcoming trip
- Student Intelligence alert
- System notification

---

# 8. Quick Add

Quick Add provides a fast way to create commonly used records without navigating through the entire application.

### Quick Add Options

```text
Quick Add
│
├── Task
├── Expense
└── Mood
```

### Example

```text
Dashboard
   │
   ▼
Quick Add
   │
   ├── Add Task ──→ Study Module
   │
   ├── Add Expense ──→ Expense Module
   │
   └── Add Mood ──→ Health Module
```

The Platform Core owns the common entry point, while the respective domain module owns the actual record creation logic.

---

# 9. Shared API Layer

Platform Core provides common API functionality used by the other CampusLife services.

### Conceptual Structure

```text
                    API Gateway
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
   User APIs       Notification APIs   Dashboard APIs
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                  Domain Services
```

Domain services include:

- To-Do & Study
- Health & Wellness
- Expense
- Travel
- Student Intelligence
- AI Voice

---

# 10. User Data Isolation

Every user-owned resource must be associated with the authenticated user.

Conceptually:

```text
User A
 │
 ├── Tasks
 ├── Health Logs
 ├── Expenses
 ├── Trips
 └── Intelligence Data

User B
 │
 ├── Tasks
 ├── Health Logs
 ├── Expenses
 ├── Trips
 └── Intelligence Data
```

A user must never be able to access another user's private records through API requests.

---

# 11. Core Data Model

A simplified relationship can be represented as:

```text
                    USER
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
    PROFILE     PREFERENCES    NOTIFICATIONS
       │
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
     TASKS         HEALTH        EXPENSES         TRIPS
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                    STUDENT INTELLIGENCE
```

The domain-specific records remain owned by their respective modules, while the user identity provides the common relationship.

---

# 12. Suggested Database Tables

The exact schema can evolve during implementation, but the Platform Core may contain tables such as:

```text
users
profiles
user_preferences
sessions
notifications
```

Domain tables should remain within their respective modules.

For example:

```text
Platform Core
├── users
├── profiles
├── user_preferences
└── notifications

Study Module
└── tasks

Health Module
└── health_logs

Expense Module
└── expenses

Travel Module
└── trips

Intelligence Module
└── student_state
```

---

# 13. API Design

The module should expose APIs for common platform functionality.

### Authentication

```text
POST   /auth/register
POST   /auth/login
POST   /auth/logout
GET    /auth/me
```

### User

```text
GET    /users/me
PATCH  /users/me
GET    /users/me/preferences
PATCH  /users/me/preferences
```

### Dashboard

```text
GET    /dashboard
```

### Notifications

```text
GET    /notifications
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
```

### Quick Add

```text
POST   /quick-add/task
POST   /quick-add/expense
POST   /quick-add/mood
```

These endpoints are an initial API design and can be adjusted according to the final backend architecture.

---

# 14. Dashboard Aggregation

The dashboard should not directly contain the business logic of every module.

Instead, it should aggregate information from domain services.

```text
                   Dashboard API
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Study Service      Health Service    Expense Service
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                   Travel Service
                         │
                         ▼
              Intelligence Service
                         │
                         ▼
                 Dashboard Response
```

This keeps the platform modular and prevents the dashboard from becoming tightly coupled to individual feature implementations.

---

# 15. Security

Platform Core is responsible for common security controls.

### Requirements

- Passwords must never be stored as plaintext.
- Authentication tokens must be securely handled.
- Protected endpoints must validate authentication.
- User-owned resources must enforce authorization.
- Sensitive configuration must be stored in environment variables/secrets.
- API input must be validated.
- Database queries must use safe parameterization/ORM mechanisms.
- Personal student data must not be exposed through unauthorized endpoints.

---

# 16. Error Handling

The module should provide consistent API error responses.

Example:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

Common categories:

```text
400 → Bad Request
401 → Unauthorized
403 → Forbidden
404 → Not Found
409 → Conflict
422 → Validation Error
500 → Internal Server Error
```

---

# 17. Logging

Platform-level logging should provide enough information to debug the system without exposing sensitive student data.

Recommended categories:

```text
Authentication Events
API Requests
Errors
Notification Events
System Events
```

Sensitive information such as passwords, authentication secrets, or private health/financial data should not be written to ordinary application logs.

---

# 18. Integration With Other Modules

Platform Core should provide common functionality without owning the internal implementation of other modules.

```text
                    PLATFORM CORE
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   Study Module     Health Module    Expense Module
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                   Travel Module
                         │
                         ▼
              Student Intelligence
                         │
                         ▼
                    AI Voice
```

All modules use the authenticated user identity and common platform services.

---

# 19. Suggested Backend Structure

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   │
│   ├── auth/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py
│   │
│   ├── users/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py
│   │
│   ├── dashboard/
│   │   ├── router.py
│   │   └── service.py
│   │
│   ├── notifications/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── models.py
│   │
│   └── database/
│       ├── database.py
│       └── base.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_dashboard.py
│   └── test_notifications.py
│
├── .env.example
├── requirements.txt
└── README.md
```

This is a suggested structure; the final structure should follow the architecture selected for the overall CampusLife repository.

---

# 20. Module Boundaries

The Platform Core should **own**:

- Authentication
- User identity
- Profile
- Preferences
- Notifications
- Dashboard aggregation
- Quick Add entry points
- Common security
- Shared API infrastructure

The Platform Core should **not own**:

- Study prediction
- Stress prediction
- Expense categorization
- Budget forecasting
- Travel itinerary generation
- Student-risk prediction
- Voice-agent intelligence

Those responsibilities belong to the respective modules.

---

# 21. Integration Contract

Every CampusLife module should be able to identify the authenticated student through a common user identity.

Conceptually:

```text
Authenticated Request
        │
        ▼
   User Identity
        │
        ├── Study
        ├── Health
        ├── Expense
        ├── Travel
        ├── Intelligence
        └── Voice
```

This provides the foundation for the Student Intelligence Engine to combine information belonging to the same student.

---

# 22. Testing

The module should include:

### Unit Tests

- Registration
- Login
- Authentication
- User profile operations
- Preference updates
- Notification creation
- Notification read state

### API Tests

- Protected endpoint access
- Invalid authentication
- Authorization
- Dashboard aggregation
- Quick Add

### Security Tests

- Unauthorized access
- Cross-user data access
- Invalid tokens
- Input validation
- Authentication edge cases

---

# 23. Definition of Done

Platform Core & User Management is considered complete when:

- [ ] Users can register
- [ ] Users can authenticate
- [ ] Protected routes work correctly
- [ ] User profiles can be managed
- [ ] User preferences can be stored
- [ ] Dashboard aggregation works
- [ ] Notifications work
- [ ] Quick Add routes to the appropriate modules
- [ ] User data is isolated
- [ ] Common API error handling is implemented
- [ ] Security controls are implemented
- [ ] Automated tests cover the core functionality
- [ ] Documentation is available

---

# 24. Role in CampusLife AI

Platform Core is the **foundation**, not the intelligence layer.

Its role can be summarized as:

```text
                  PLATFORM CORE
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Identity        Access        Communication
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              CampusLife Modules
                       │
                       ▼
             Student Intelligence
                       │
                       ▼
               AI Voice Assistant
```

Every other part of CampusLife AI depends on this module for a consistent user identity, secure access, common platform services, and a unified application experience.