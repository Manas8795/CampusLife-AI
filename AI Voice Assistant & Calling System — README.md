# CampusLife AI — AI Voice Assistant & Calling System

## 1. Overview

The **AI Voice Assistant & Calling System** is the voice-interaction layer of CampusLife AI.

It provides students with a natural voice interface through which they can interact with CampusLife without manually navigating the platform.

The module supports:

- Voice conversations
- Speech-to-text
- Natural-language understanding
- CampusLife information retrieval
- Action execution
- Text-to-speech
- Outbound AI calls
- Reminder calls
- Event-based calls
- Student Intelligence integration

The module acts as an interface over the existing CampusLife services rather than independently owning academic, health, financial, or travel data.

---

# 2. Module Responsibilities

```text
AI Voice Assistant & Calling
│
├── Voice Input
├── Speech-to-Text
├── Intent Detection
├── Context Management
├── Tool / API Calling
├── AI Response Generation
├── Text-to-Speech
├── Voice Conversations
├── Outbound AI Calls
├── Call Scheduling
├── Call State Management
└── Student Intelligence Integration
```

---

# 3. Core Concept

The voice assistant should work as an orchestration layer.

```text
Student
   │
   ▼
Voice
   │
   ▼
Speech-to-Text
   │
   ▼
AI Agent
   │
   ├── Study Planner
   ├── Health & Wellness
   ├── Expense Manager
   ├── Travel Planner
   └── Student Intelligence
   │
   ▼
Action / Information
   │
   ▼
AI Response
   │
   ▼
Text-to-Speech
   │
   ▼
Student
```

The assistant should not directly manipulate database tables belonging to other modules.

Instead, it should use their APIs or defined service interfaces.

---

# 4. Why This Module Exists

CampusLife contains several different modules.

Without a unified interface, students need to navigate multiple screens.

The Voice Assistant provides a single interaction point.

Instead of:

```text
Open Study Planner
      ↓
Find Tasks
      ↓
Check Deadline
      ↓
Open Health
      ↓
Check Sleep
```

the student can ask:

> "What do I need to focus on today?"

The Voice Assistant can query Student Intelligence and return a combined response.

---

# 5. Voice Interaction Modes

The system can support multiple interaction modes.

```text
Voice Assistant
│
├── In-App Voice
├── Web Voice
├── Mobile Voice
└── Phone Call
```

The initial implementation can focus on **in-app voice** and **outbound phone calls**, with other interfaces added later.

---

# 6. In-App Voice Assistant

The student can press a microphone button and speak.

```text
Student
   │
   ▼
Microphone
   │
   ▼
Audio Stream
   │
   ▼
Speech-to-Text
   │
   ▼
AI Agent
   │
   ▼
CampusLife APIs
   │
   ▼
Response
   │
   ▼
Text-to-Speech
   │
   ▼
Audio
```

Example:

> "What assignments do I have due this week?"

The assistant queries the Study Planner and responds using voice.

---

# 7. Speech-to-Text

Speech-to-text converts spoken audio into text.

```text
Audio
  │
  ▼
Speech Recognition
  │
  ▼
Text
```

Example:

```text
Audio:
"I have an exam tomorrow, what should I study?"

STT Output:
"I have an exam tomorrow, what should I study?"
```

The STT provider should be abstracted behind a service interface.

---

# 8. Intent Detection

The system identifies what the student is trying to accomplish.

Example:

```text
User:
"What assignments are due tomorrow?"
```

Possible intent:

```json
{
  "intent": "GET_UPCOMING_TASKS",
  "date": "tomorrow"
}
```

Another example:

```text
User:
"How much have I spent this month?"
```

Intent:

```json
{
  "intent": "GET_MONTHLY_SPENDING"
}
```

---

# 9. CampusLife Tool Calling

The AI agent should have access to controlled tools.

```text
AI Agent
   │
   ├── get_tasks()
   ├── get_study_plan()
   ├── get_wellness_state()
   ├── get_expenses()
   ├── get_budget()
   ├── get_trips()
   ├── get_student_insights()
   └── create_task()
```

The actual tool set should be limited to approved operations.

---

# 10. Tool Calling Architecture

```text
Voice Input
    │
    ▼
Speech-to-Text
    │
    ▼
AI Agent
    │
    ▼
Intent / Tool Selection
    │
    ├──────► Study API
    │
    ├──────► Health API
    │
    ├──────► Expense API
    │
    ├──────► Travel API
    │
    └──────► Intelligence API
                 │
                 ▼
              Result
                 │
                 ▼
             AI Agent
                 │
                 ▼
              Response
```

This keeps the voice layer decoupled from individual modules.

---

# 11. Context Management

The assistant should understand the context of the conversation.

Example:

```text
Student:
"What exams do I have?"

Assistant:
"You have a Database Systems exam on Friday."

Student:
"How should I prepare for it?"

```

The second request should inherit the relevant context from the first conversation.

```text
Conversation Context
│
├── Current Subject
├── Current Task
├── Current Date
├── User Intent
└── Previous Tool Results
```

---

# 12. Conversation State

A conversation can be represented as:

```text
CONVERSATION
│
├── Conversation ID
├── User ID
├── Started At
├── Last Activity
└── Messages
       │
       ├── USER
       └── ASSISTANT
```

Only the context required for future reasoning should be retained.

---

# 13. Natural Language Action Execution

The assistant can perform permitted actions.

Example:

> "Add a task to finish my DB assignment tomorrow at 6 PM."

Processing:

```text
Voice
 │
 ▼
STT
 │
 ▼
Intent Detection
 │
 ▼
CREATE_TASK
 │
 ▼
Study Planner API
 │
 ▼
Task Created
 │
 ▼
AI Response
 │
 ▼
TTS
```

Response:

> "I've added your DB assignment for tomorrow at 6 PM."

---

# 14. Confirmation for Important Actions

Actions with meaningful consequences should require confirmation.

For example:

```text
Student:
"Delete my entire study plan."

Assistant:
"This will remove your current study plan. Do you want to continue?"
```

```text
Student:
"Yes."

      ↓

Execute Action
```

The system should define which tools require confirmation.

---

# 15. Read vs Write Operations

Tools should be classified into:

```text
Tools
│
├── READ
│   ├── Get Tasks
│   ├── Get Expenses
│   ├── Get Budget
│   ├── Get Wellness
│   └── Get Trips
│
└── WRITE
    ├── Create Task
    ├── Update Task
    ├── Create Expense
    ├── Create Trip
    └── Other Mutations
```

Write operations should have stricter validation and authorization.

---

# 16. Text-to-Speech

After the AI generates a response, it is converted back into audio.

```text
AI Response
     │
     ▼
Text-to-Speech
     │
     ▼
Audio
     │
     ▼
Student
```

The TTS layer should support configurable:

- Voice
- Language
- Speaking speed
- Output format

---

# 17. Outbound AI Calling

The distinctive feature of this module is the ability to initiate an AI-powered phone call.

Example:

```text
Scheduled Event
       │
       ▼
Calling Service
       │
       ▼
Student's Phone
       │
       ▼
AI Voice Conversation
```

A telephony provider such as Twilio can be used as the communication layer.

The telephony provider handles the phone connection, while CampusLife controls the AI logic.

---

# 18. AI Calling Architecture

```text
CampusLife
    │
    ▼
Call Scheduler
    │
    ▼
Calling Service
    │
    ▼
Telephony Provider
    │
    ▼
Student Phone
    │
    ▼
Voice Input
    │
    ▼
Speech-to-Text
    │
    ▼
AI Agent
    │
    ▼
Response
    │
    ▼
Text-to-Speech
    │
    ▼
Phone Call
```

---

# 19. Calling Use Cases

Potential use cases include:

### Study Reminder

```text
Exam Tomorrow
     │
     ▼
Scheduled Call
     │
     ▼
AI:
"You have your DB exam tomorrow.
Would you like me to review your study plan?"
```

### Task Reminder

```text
Overdue Task
     │
     ▼
AI Call
     │
     ▼
"Your assignment is still pending.
Would you like to reschedule it?"
```

### Wellness Check-In

```text
Wellness Signal
      │
      ▼
Scheduled Check-In
      │
      ▼
"How are you feeling today?"
```

### Financial Alert

```text
Budget Threshold
      │
      ▼
Optional AI Call
      │
      ▼
"You've used most of your monthly budget."
```

Calls should be configurable and opt-in.

---

# 20. Calling Consent

Phone calling requires explicit student consent.

The system should store:

```text
Voice Calling Preferences
│
├── Calling Enabled
├── Phone Number
├── Preferred Calling Time
├── Allowed Call Types
└── Consent Status
```

Students should be able to disable AI calls.

---

# 21. Call Scheduling

Calls can be scheduled based on events.

```text
Trigger
   │
   ├── Exam approaching
   ├── Task overdue
   ├── Reminder
   ├── Wellness check
   └── User-created reminder
   │
   ▼
Call Scheduler
   │
   ▼
Scheduled Call
```

The scheduler should respect:

- User preferences
- Quiet hours
- Consent
- Call frequency limits

---

# 22. Call State Machine

Each call should have a clear state.

```text
SCHEDULED
    │
    ▼
QUEUED
    │
    ▼
INITIATED
    │
    ├── FAILED
    │
    ▼
RINGING
    │
    ▼
CONNECTED
    │
    ▼
IN_PROGRESS
    │
    ▼
COMPLETED
```

Additional states can include:

```text
NO_ANSWER
BUSY
CANCELLED
```

---

# 23. Call Records

A call record can contain:

```text
CALL
│
├── ID
├── User ID
├── Phone Number Reference
├── Call Type
├── Trigger
├── Scheduled Time
├── Started At
├── Ended At
├── Duration
├── Status
└── Outcome
```

The system should avoid storing unnecessary sensitive conversation content.

---

# 24. AI Calling Conversation

A call can contain multiple turns.

```text
AI:
"You have a DB assignment due tomorrow.
Would you like to work on it tonight?"

Student:
"Yes, remind me at 8."

AI:
"Okay. I'll set a reminder for 8 PM."
```

The assistant can then invoke the relevant Study Planner or Reminder API.

---

# 25. Calling + Student Intelligence

The Student Intelligence Engine can trigger contextual calls.

```text
Student Intelligence
        │
        ▼
Important Insight
        │
        ▼
Should Student Be Notified?
        │
        ▼
Calling Policy
        │
        ▼
AI Call
```

Example:

```text
Exam Approaching
      +
High Pending Tasks
      +
Low Recent Completion
      ↓
Student Intelligence
      ↓
High-Priority Insight
      ↓
AI Voice Call
```

The Intelligence Engine should determine the **reason for the notification**; the Voice module determines **how to communicate it**.

---

# 26. Voice + Student Intelligence

The voice assistant can also query the intelligence layer directly.

Example:

> "How am I doing overall?"

The assistant can retrieve:

```text
Academic State
+
Wellness State
+
Financial State
+
Travel State
```

and produce a concise summary.

---

# 27. Proactive Voice Interaction

The module supports two types of interaction.

### Reactive

Student initiates:

```text
Student
   ↓
Voice Assistant
```

### Proactive

CampusLife initiates:

```text
CampusLife Event
       ↓
Student Intelligence
       ↓
Calling Policy
       ↓
AI Voice Call
```

This distinction should be reflected in the architecture.

---

# 28. Calling Policy Engine

Not every event should result in a phone call.

The Calling Policy Engine can decide whether a call is appropriate.

```text
Event
 │
 ▼
Calling Policy
 │
 ├── User consent?
 ├── Quiet hours?
 ├── Severity?
 ├── Already notified?
 ├── Call frequency?
 └── User preference?
 │
 ▼
Call / Do Not Call
```

This prevents excessive or unnecessary calls.

---

# 29. Notification Hierarchy

The system can use different communication levels.

```text
Priority
│
├── LOW
│    └── In-App Notification
│
├── MEDIUM
│    └── Push / Email
│
└── HIGH
     └── Optional AI Voice Call
```

The exact policy can be configured later.

---

# 30. API Design

A possible initial API structure:

### Voice

```text
POST   /voice/session
POST   /voice/transcribe
POST   /voice/respond
POST   /voice/synthesize
```

### Assistant

```text
POST   /assistant/message
GET    /assistant/conversations
GET    /assistant/conversations/{id}
```

### Calls

```text
POST   /calls
GET    /calls
GET    /calls/{id}
POST   /calls/{id}/cancel
```

### Calling Preferences

```text
GET    /voice/preferences
PATCH  /voice/preferences
```

These endpoints are an initial design and can change during implementation.

---

# 31. Suggested Data Model

```text
USER
 │
 ├── VOICE_PREFERENCES
 │     ├── calling_enabled
 │     ├── preferred_time
 │     ├── consent_status
 │     └── updated_at
 │
 ├── CONVERSATION
 │     ├── id
 │     ├── user_id
 │     ├── started_at
 │     └── last_activity
 │
 ├── MESSAGE
 │     ├── conversation_id
 │     ├── role
 │     ├── content
 │     └── created_at
 │
 └── CALL
       ├── id
       ├── user_id
       ├── type
       ├── trigger
       ├── scheduled_at
       ├── started_at
       ├── ended_at
       ├── status
       └── outcome
```

---

# 32. Suggested Backend Structure

```text
backend/
│
├── app/
│   └── voice/
│       ├── router.py
│       ├── service.py
│       ├── schemas.py
│       ├── models.py
│       ├── session.py
│       ├── tools.py
│       └── policy.py
│
├── ai/
│   ├── agent.py
│   ├── prompts.py
│   └── context.py
│
├── speech/
│   ├── stt.py
│   └── tts.py
│
├── telephony/
│   ├── provider.py
│   ├── calls.py
│   └── webhooks.py
│
└── tests/
    ├── test_voice.py
    ├── test_agent.py
    ├── test_calls.py
    └── test_call_policy.py
```

---

# 33. Provider Abstraction

The application should not tightly couple the core system to Twilio.

Use an interface such as:

```text
TelephonyProvider
│
├── initiate_call()
├── end_call()
├── get_call_status()
└── handle_webhook()
```

Then:

```text
TelephonyProvider
       │
       ├── TwilioProvider
       └── FutureProvider
```

This allows the telephony provider to be changed without rewriting the Voice module.

---

# 34. Webhooks

The telephony provider can send events back to CampusLife.

Examples:

```text
CALL_INITIATED
CALL_RINGING
CALL_ANSWERED
CALL_COMPLETED
CALL_FAILED
```

Example:

```text
Twilio
  │
  ▼
Webhook
  │
  ▼
CampusLife API
  │
  ▼
Update Call State
```

Webhook endpoints must authenticate and validate incoming requests.

---

# 35. Error Handling

The module should handle:

### Speech Recognition Failure

```text
Audio
 ↓
STT Failure
 ↓
Ask Student to Repeat
```

### AI Failure

```text
Input
 ↓
AI Failure
 ↓
Fallback Response
```

### Telephony Failure

```text
Call Request
 ↓
Provider Failure
 ↓
Retry / Mark Failed
```

### No Answer

```text
Call
 ↓
No Answer
 ↓
Update Status
 ↓
Optional Retry According to Policy
```

The system should avoid repeated calls without explicit policy.

---

# 36. Security

The Voice module handles highly sensitive information.

Requirements:

- Authenticate voice sessions
- Authorize tool calls
- Validate all write operations
- Secure telephony credentials
- Protect provider API keys
- Secure webhook endpoints
- Protect conversation data
- Avoid unnecessary audio retention
- Restrict access to call records

The AI agent must never be allowed unrestricted database access.

---

# 37. AI Safety Boundaries

The voice assistant should operate within clearly defined capabilities.

It should not:

- Invent CampusLife data
- Claim an action succeeded when it failed
- Modify data without authorization
- Expose another student's information
- Make unsupported medical or financial claims
- Execute dangerous or irreversible operations without confirmation

For sensitive domains, the assistant should rely on structured module data.

---

# 38. Voice Interaction Logging

The system can log operational metadata such as:

```text
Conversation ID
Intent
Tool Used
Tool Success
Call Status
Response Latency
```

Avoid storing full audio or conversation transcripts indefinitely unless there is a clear product requirement and appropriate consent.

---

# 39. Performance

Voice interaction requires low latency.

The pipeline should minimize unnecessary sequential operations.

```text
Audio
 ↓
STT
 ↓
Intent / Agent
 ↓
Tool
 ↓
Response
 ↓
TTS
```

Caching can be considered for frequently accessed non-sensitive information.

---

# 40. Testing

### Voice Tests

- Speech-to-text
- Intent recognition
- Context handling
- Tool selection
- Response generation
- Text-to-speech

### Tool Tests

- Read operations
- Write operations
- Authorization
- Confirmation requirements

### Calling Tests

- Call creation
- Call scheduling
- Call cancellation
- Call status
- Provider webhook handling
- No-answer handling
- Failed-call handling

### Integration Tests

- Voice → Study Planner
- Voice → Expense Manager
- Voice → Health
- Voice → Travel
- Voice → Student Intelligence

---

# 41. Definition of Done

The AI Voice Assistant & Calling System is considered complete when:

- [ ] In-app voice input works
- [ ] Speech-to-text works
- [ ] AI intent detection works
- [ ] Contextual conversations work
- [ ] CampusLife tools can be invoked
- [ ] Read operations work
- [ ] Write operations are validated
- [ ] Important write operations require confirmation
- [ ] Text-to-speech works
- [ ] Voice preferences can be configured
- [ ] Phone calling can be initiated
- [ ] Calls can be scheduled
- [ ] Call state is tracked
- [ ] Provider webhooks are handled
- [ ] Failed calls are handled
- [ ] Calling consent is enforced
- [ ] Quiet hours are respected
- [ ] Calling frequency is controlled
- [ ] Student Intelligence can trigger eligible calls
- [ ] Voice assistant can query Student Intelligence
- [ ] User-level authorization is enforced
- [ ] Telephony credentials are secured
- [ ] Automated tests are implemented

---

# 42. Role in CampusLife AI

The AI Voice Assistant & Calling System acts as the **primary conversational interface** for CampusLife.

```text
                         CAMPUSLIFE
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
     Study                 Health                Expense
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                           Travel
                             │
                             ▼
                  Student Intelligence
                             │
                             ▼
                     AI VOICE LAYER
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
          Voice Assistant            AI Calling
                │                         │
                ▼                         ▼
           Student Input            Proactive Contact
```

The module therefore has three primary roles:

1. **Provide a natural voice interface for interacting with CampusLife.**
2. **Allow the AI to execute authorized actions across CampusLife modules.**
3. **Enable optional proactive AI phone interactions driven by important student events and Student Intelligence.**

The combination of **voice AI + tool calling + cross-module context + outbound AI calling** makes this module the primary interaction layer connecting the student's CampusLife data with a conversational assistant.