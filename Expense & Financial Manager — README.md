# CampusLife AI — Expense & Financial Manager

## 1. Overview

The **Expense & Financial Manager** is the financial-management module of CampusLife AI.

It allows students to record, organize, and analyze their expenses while using **OCR, Generative AI, and Machine Learning** to reduce manual entry and provide financial forecasting.

The module combines:

- Manual expense tracking
- Receipt image upload
- OCR-based text extraction
- AI-powered receipt parsing
- Automatic expense categorization
- Spending history
- Budget monitoring
- Monthly budget forecasting
- Predicted out-of-cash date
- Financial signals for the Student Intelligence Engine

The module is intended for **personal financial organization and forecasting**, not professional financial advice.

---

# 2. Module Responsibilities

```text id="p7x4mk"
Expense & Financial Manager
│
├── Expense Management
├── Receipt Management
├── OCR Processing
├── AI Receipt Parsing
├── Expense Categorization
├── Spending Analytics
├── Budget Management
├── Budget Forecasting
├── Out-of-Cash Prediction
└── Student Intelligence Integration
```

The module owns student expense and budgeting functionality.

It does **not** own:

- Authentication
- User identity
- General notifications
- Academic task management
- Health tracking
- Travel planning
- Cross-domain Student Intelligence

Those responsibilities belong to other CampusLife modules.

---

# 3. Core Features

### Expense Management

- Add expenses manually
- Edit expenses
- Delete expenses
- Categorize expenses
- View expense history
- Filter expenses
- Track spending over time

### Receipt Processing

- Upload receipt images
- Store receipt images
- Extract text using OCR
- Parse receipt information using GenAI
- Allow student confirmation before saving

### Financial Intelligence

- Calculate spending trends
- Monitor budgets
- Forecast monthly spending
- Estimate remaining budget
- Predict potential out-of-cash dates

---

# 4. Expense Management

Students should be able to manually record expenses.

### Expense Lifecycle

```text id="m4q9cz"
Create Expense
      │
      ▼
Validate
      │
      ▼
Categorize
      │
      ▼
Store
      │
      ▼
Expense History
      │
      ▼
Analytics / Forecasting
```

An expense can originate from:

- Manual entry
- Receipt processing

Both sources should eventually produce the same structured expense representation.

---

# 5. Expense Data

A basic expense record can contain:

```text id="h6k3vp"
Expense
│
├── ID
├── User ID
├── Amount
├── Currency
├── Category
├── Merchant
├── Description
├── Date
├── Payment Method
├── Source
├── Receipt ID
└── Created At
```

The exact fields can be adjusted during implementation.

---

# 6. Expense Categories

The system should support a configurable set of expense categories.

An initial set could include:

```text id="t8n5qr"
Expense Categories
│
├── Food
├── Transport
├── Education
├── Shopping
├── Entertainment
├── Accommodation
├── Travel
├── Bills
└── Other
```

The category system should remain extensible so additional categories can be added later.

---

# 7. Manual Expense Entry

Students should be able to enter an expense without uploading a receipt.

Example:

```text id="r4w8ns"
Amount:       ₹250
Merchant:     College Canteen
Category:     Food
Date:         2026-10-05
Description:  Lunch
```

The backend validates the data before storing it.

```text id="x3m7qp"
Frontend
   │
   ▼
Expense API
   │
   ▼
Validation
   │
   ▼
PostgreSQL
```

---

# 8. Receipt Processing

Receipt processing is one of the major AI-assisted features of the module.

### Pipeline

```text id="v9k2ds"
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
Expense Database
```

The student should be able to review the extracted information before the expense is permanently recorded.

---

# 9. Receipt Upload

Students can upload or capture a receipt image.

Supported inputs may include:

- JPG
- JPEG
- PNG
- Other supported image formats

The backend should validate:

- File type
- File size
- Upload ownership
- Storage status

### Upload Flow

```text id="k5v8yc"
Student
   │
   ▼
Upload Receipt
   │
   ▼
Validation
   │
   ▼
Cloud Storage
   │
   ▼
Receipt ID
```

---

# 10. OCR Processing

OCR converts the receipt image into machine-readable text.

```text id="s8f4nx"
Receipt Image
      │
      ▼
     OCR
      │
      ▼
Raw Receipt Text
```

Example:

```text id="c2q7mr"
ABC MART
----------------
Milk       ₹60
Bread      ₹45
Eggs       ₹80
----------------
Total     ₹185
```

OCR output should be treated as an intermediate representation rather than the final expense record.

---

# 11. AI Receipt Parsing

GenAI converts OCR text into structured information.

### Input

```text id="y7m3kp"
Raw OCR Text
      │
      ▼
     LLM
```

### Output

```json id="f4r9wx"
{
  "merchant": "ABC MART",
  "items": [
    {
      "name": "Milk",
      "amount": 60
    },
    {
      "name": "Bread",
      "amount": 45
    },
    {
      "name": "Eggs",
      "amount": 80
    }
  ],
  "total": 185,
  "category": "Food"
}
```

The backend should validate the structured output before storing it.

---

# 12. Student Confirmation

AI-generated expense information should not automatically be treated as authoritative.

The recommended flow is:

```text id="n6x2pq"
OCR
 │
 ▼
GenAI Parsing
 │
 ▼
Structured Expense
 │
 ▼
Student Review
 │
 ├── Correct
 │
 └── Edit
 │
 ▼
Save
```

This allows the student to correct:

- Merchant
- Amount
- Category
- Date
- Items

before the final database insertion.

---

# 13. Expense History

The module should provide a historical view of expenses.

Students should be able to:

- View expenses
- Search expenses
- Filter by category
- Filter by date
- Sort by amount/date
- View receipt information

Example:

```text id="u5j8rc"
October Expenses

Food           ₹4,250
Transport      ₹1,800
Education      ₹2,400
Entertainment  ₹1,200
Other          ₹950
---------------------
Total          ₹10,600
```

---

# 14. Spending Analytics

The module can calculate useful spending metrics.

### Metrics

- Total spending
- Daily spending
- Weekly spending
- Monthly spending
- Category-wise spending
- Average daily spending
- Spending trend
- Budget utilization

```text id="q3v7mn"
Expense History
      │
      ▼
Analytics Engine
      │
 ┌────┼───────────────┐
 ▼    ▼               ▼
Daily Category      Monthly
Spend   Spend        Spend
```

---

# 15. Budget Management

Students can define a monthly budget.

Example:

```text id="j8m4cz"
Monthly Budget
      │
      ├── Total: ₹15,000
      │
      ├── Food: ₹5,000
      ├── Transport: ₹2,500
      ├── Education: ₹3,000
      └── Other: ₹4,500
```

The system can compare actual spending against the configured budget.

---

# 16. Budget Utilization

Example:

```text id="r7p2xd"
Monthly Budget     → ₹15,000
Current Spending   → ₹10,600
Remaining          → ₹4,400
Utilization        → 70.7%
```

The frontend can represent this using a budget progress indicator.

---

# 17. Budget Forecasting

The module can use historical expense data to estimate future spending.

### Pipeline

```text id="z5k8qs"
Historical Expenses
       │
       ▼
Feature Engineering
       │
       ▼
Time-Series / ML Model
       │
       ▼
Future Spending Forecast
       │
       ▼
Budget Analysis
```

Possible outputs include:

- Expected monthly spending
- Expected remaining spending
- Expected budget overrun
- Expected daily spending

---

# 18. Out-of-Cash Prediction

One of the more advanced features of the module is estimating when the student's available funds may be exhausted.

### Inputs

```text id="b4n7vp"
Current Balance
       +
Historical Spending
       +
Recent Spending Trend
       +
Expected Future Expenses
       │
       ▼
Forecasting Model
       │
       ▼
Predicted Out-of-Cash Date
```

Example:

```text id="m9c5xr"
Current Balance:          ₹4,200
Average Daily Spending:   ₹350

Estimated Remaining Days: ~12
Predicted Out-of-Cash:    17 Oct
```

The exact calculation should depend on the forecasting model and available data.

---

# 19. Forecasting Architecture

The forecasting system should remain separate from the OCR and GenAI components.

```text id="v2s8yk"
Receipt / Manual Expenses
           │
           ▼
      Expense Database
           │
           ▼
     Historical Dataset
           │
           ▼
     Feature Engineering
           │
           ▼
      Forecasting Model
           │
      ┌────┴─────────┐
      ▼              ▼
Spending Forecast  Risk
      │              │
      └──────┬───────┘
             ▼
        Expense Module
```

GenAI should not be used as the numerical forecasting model.

---

# 20. Student Intelligence Integration

Expense information becomes an important input to the Student Intelligence Engine.

```text id="q8m4td"
                 EXPENSE MODULE
                       │
       ┌───────────────┼──────────────┐
       ▼               ▼              ▼
   Spending         Budget        Forecast
    Trends          Status       Out-of-Cash
       │               │              │
       └───────────────┼──────────────┘
                       ▼
              Student Intelligence
```

Student Intelligence can combine financial signals with other domains.

### Example

```text id="w3k7pn"
Upcoming Exam
      +
High Study Workload
      +
Increasing Spending
      +
Low Remaining Budget
      ↓
Student Intelligence
      ↓
Cross-Domain Insight
```

The Expense module provides the financial signals; Student Intelligence determines whether they form part of a broader student situation.

---

# 21. Travel Integration

The Expense module can provide financial context to the Travel Planner.

Example:

```text id="p6v9xr"
Current Budget
     +
Existing Spending
     +
Upcoming Expenses
     ↓
Available Travel Budget
     ↓
Travel Planner
```

This allows travel recommendations to consider the student's actual financial situation rather than using only a manually entered travel budget.

---

# 22. Notifications Integration

The module can generate events for the shared Notification Service.

Examples:

- Budget nearing limit
- Predicted budget overrun
- Unusual spending
- Predicted low balance
- Important financial milestone

```text id="d8m5qy"
Expense Module
     │
     ▼
Financial Event
     │
     ▼
Notification Service
     │
     ▼
Student
```

The notification infrastructure remains owned by Platform Core.

---

# 23. API Design

A possible initial API structure:

### Expenses

```text id="s4k8vx"
POST   /expenses
GET    /expenses
GET    /expenses/{id}
PATCH  /expenses/{id}
DELETE /expenses/{id}
```

### Receipts

```text id="c7n3mq"
POST   /receipts/upload
GET    /receipts
GET    /receipts/{id}
DELETE /receipts/{id}
POST   /receipts/{id}/process
```

### Budget

```text id="h5r8zy"
POST   /budget
GET    /budget
PATCH  /budget
```

### Analytics

```text id="m2q7xd"
GET    /expenses/summary
GET    /expenses/trends
GET    /expenses/categories
```

### Forecasting

```text id="p8v4kn"
GET    /expenses/forecast
GET    /expenses/out-of-cash
```

These endpoints are an initial design and can be modified as implementation progresses.

---

# 24. Suggested Data Model

A possible relational structure:

```text id="y6r3mc"
USER
 │
 ├── EXPENSE
 │     ├── id
 │     ├── user_id
 │     ├── amount
 │     ├── currency
 │     ├── merchant
 │     ├── category
 │     ├── description
 │     ├── expense_date
 │     ├── payment_method
 │     ├── source
 │     └── created_at
 │
 ├── RECEIPT
 │     ├── id
 │     ├── user_id
 │     ├── storage_url
 │     ├── ocr_text
 │     ├── processing_status
 │     └── created_at
 │
 └── BUDGET
       ├── id
       ├── user_id
       ├── month
       ├── total_budget
       └── created_at
```

Forecast results can either be calculated dynamically or stored separately.

---

# 25. Receipt Processing State

Receipt processing should maintain explicit states.

```text id="k9w5zr"
UPLOADED
    │
    ▼
PROCESSING
    │
    ├── FAILED
    │
    ▼
OCR_COMPLETE
    │
    ▼
AI_PARSED
    │
    ▼
AWAITING_CONFIRMATION
    │
    ▼
CONFIRMED
```

This makes asynchronous processing and error handling easier.

---

# 26. Suggested Backend Structure

```text id="v7m2qc"
backend/
│
├── app/
│   └── expenses/
│       ├── router.py
│       ├── service.py
│       ├── schemas.py
│       ├── models.py
│       └── dependencies.py
│
├── ai/
│   └── receipt_parser.py
│
├── ocr/
│   ├── service.py
│   └── processor.py
│
├── ml/
│   └── budget/
│       ├── model.py
│       ├── features.py
│       ├── predictor.py
│       └── preprocessing.py
│
└── tests/
    ├── test_expenses.py
    ├── test_receipts.py
    ├── test_ocr.py
    └── test_forecasting.py
```

The final structure should follow the overall CampusLife repository architecture.

---

# 27. AI Architecture

The receipt AI pipeline should be separated into distinct stages.

```text id="n8q4xs"
Receipt Image
     │
     ▼
   OCR Service
     │
     ▼
 OCR Text
     │
     ▼
Receipt Parser
     │
     ▼
Structured JSON
     │
     ▼
Schema Validation
     │
     ▼
Student Confirmation
```

The AI parser should not directly write unvalidated output to the database.

---

# 28. Forecasting Model

The budget forecasting model should use historical expense records.

Possible features include:

- Daily spending
- Rolling average spending
- Category spending
- Recent spending trend
- Days remaining in month
- Current budget utilization
- Historical monthly spending

```text id="r5c8yv"
Expense History
      │
      ▼
Feature Engineering
      │
      ▼
Forecasting Model
      │
      ├── Expected Spending
      ├── Budget Overrun Risk
      └── Out-of-Cash Estimate
```

The exact model should be selected after evaluating the available dataset and forecasting requirements.

---

# 29. Explainability

Financial predictions should provide understandable information.

Instead of:

> "Budget risk: 87%."

the application should provide context such as:

> "Your recent daily spending is higher than your average and your current monthly budget is already 72% utilized."

The explanation should be based on actual stored financial metrics.

---

# 30. Security & Privacy

Financial information is sensitive personal data.

Requirements:

- Authenticate all expense endpoints
- Enforce user-level authorization
- Prevent cross-user access
- Secure receipt storage
- Protect receipt URLs
- Avoid logging complete receipt contents
- Avoid logging financial information unnecessarily
- Secure API credentials
- Encrypt data in transit
- Store secrets securely

A student must only be able to access their own:

- Expenses
- Receipts
- Budgets
- Forecasts
- Financial analytics

---

# 31. File Storage Security

Receipt images should not be exposed through unrestricted public storage.

Recommended flow:

```text id="c5m8qn"
Student
   │
   ▼
Authenticated API
   │
   ▼
Private Storage
   │
   ▼
Signed / Authorized Access
```

The exact storage implementation can use the cloud-storage system selected for the overall project.

---

# 32. Validation

The backend should validate:

- Expense amount
- Currency
- Expense date
- Category
- Receipt file type
- Receipt file size
- OCR output
- AI-generated receipt data
- Budget values

The system should reject invalid or inconsistent financial records.

---

# 33. Testing

### Expense Tests

- Create expense
- Retrieve expense
- Update expense
- Delete expense
- Category handling
- Date handling
- Amount validation

### Receipt Tests

- Receipt upload
- File validation
- OCR processing
- AI parsing
- Structured-output validation
- Student confirmation
- Processing failure

### Forecasting Tests

- Feature generation
- Forecast generation
- Missing historical data
- Insufficient data
- Out-of-cash calculation

### Authorization Tests

- User can access own expenses
- User cannot access another user's expenses
- User cannot access another user's receipts
- User cannot modify another user's budget

---

# 34. Edge Cases

The system should handle cases such as:

### No historical expenses

```text
No History
    ↓
Insufficient Data
    ↓
Do not produce unreliable forecast
```

### Invalid receipt

```text
Receipt
  ↓
OCR Failure
  ↓
Processing Failed
  ↓
Allow Manual Entry
```

### AI parsing error

```text
OCR Text
   ↓
AI Parser
   ↓
Invalid Output
   ↓
Validation Failure
   ↓
Ask Student to Enter / Correct Data
```

### Very high expense

The system should flag unusual values for confirmation rather than silently accepting a potentially incorrect OCR result.

---

# 35. Definition of Done

The Expense & Financial Manager is considered complete when:

- [ ] Manual expenses can be created
- [ ] Expenses can be edited
- [ ] Expenses can be deleted
- [ ] Expenses can be categorized
- [ ] Expense history works
- [ ] Receipts can be uploaded
- [ ] Receipt images are securely stored
- [ ] OCR extraction works
- [ ] AI receipt parsing works
- [ ] AI output is validated
- [ ] Students can confirm/edit parsed expenses
- [ ] Monthly budgets can be configured
- [ ] Spending analytics work
- [ ] Budget utilization is calculated
- [ ] Spending forecasts work
- [ ] Out-of-cash prediction works when sufficient data exists
- [ ] Financial signals can be consumed by Student Intelligence
- [ ] Travel planning can consume relevant financial context
- [ ] Financial notifications can be generated
- [ ] User-level authorization is enforced
- [ ] Sensitive financial data is protected
- [ ] Automated tests are implemented

---

# 36. Role in CampusLife AI

The Expense & Financial Manager provides the **financial context** required by the larger CampusLife system.

```text id="z4m7xp"
              EXPENSE & FINANCIAL
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Expenses        Budget        Forecast
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Financial Signals
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
Student Intelligence          Travel Planner
          │
          ▼
 Cross-Domain Analysis
          │
          ▼
 Personalized Insight
          │
          ▼
 Proactive Assistant
          │
          ▼
       AI Voice
```

The module therefore has two primary roles:

1. **Provide students with practical expense tracking, receipt automation, budgeting, and financial forecasting.**
2. **Provide reliable financial signals to the Student Intelligence Engine and relevant context to other CampusLife modules.**

The combination of **OCR + GenAI + financial analytics + forecasting** makes this module one of the technically richer components of CampusLife AI.