# AlphaRatio Scanner — AI Engineering Guidelines

---

# 1. Engineering Philosophy

The codebase should prioritize:

* simplicity
* modularity
* readability
* extensibility
* predictable behavior
* maintainability

Avoid unnecessary abstraction.

### 1.1 Applied Engineering Principles

To maintain a resilient and professional system, the following principles are strictly enforced:

* **Defensive Programming & Robust I/O**: Never assume input files or third-party responses are perfectly formatted. Use robust, format-aware tools (e.g., `utf-8-sig` for YAML parsing) to handle silent failures gracefully.
* **Smart Recovery & Self-Healing**: Pipelines should interrogate their own state (e.g., database row counts) to determine execution paths rather than relying on hardcoded flags. If data is missing, the system should attempt to recover it automatically.
* **Fail-Fast & Explicit Constraints**: Reject "ghost data" early. Operational tools (like CSV importers) must validate inputs against the Single Source of Truth (`config.yaml`) and halt immediately if unauthorized symbols are found.
* **Data Integrity & Traceability**: Ensure the database schema always reflects the configuration. Automate boilerplate synchronizations during edge-case or fallback workflows to maintain referential integrity.

---

# 2. Architectural Rules

## 2.1 Separation of Concerns

Strictly separate:

* data ingestion
* calculations
* persistence
* scanner logic
* presentation layer

---

## 2.2 No Hidden Business Logic

Business logic must NOT exist inside:

* Streamlit UI code
* plotting code
* ORM models

Business logic belongs in dedicated service modules.

---

## 2.3 Stateless Engines

Scanner engines should remain:

* deterministic
* stateless
* reproducible

Avoid hidden runtime state.

---

# 3. Database Rules

## 3.1 Persist Computed Data

Persist:

* ratios
* indicators
* rankings
* ATH/52WH metrics
* watchlist states

Do not dynamically recompute indicators inside dashboard views.

---

## 3.2 Avoid Giant Tables

Prefer normalized tables.

Avoid:

* massive denormalized tables
* duplicated columns
* repeated calculations

---

# 4. Code Organization

## 4.1 Preferred Structure

```text
/app
  /config
  /data
  /database
  /engines
  /services
  /alerts
  /dashboard
  /charts
  /utils
```

---

## 4.2 Service Isolation

Each major responsibility should have:

* isolated service layer
* clear inputs
* clear outputs

---

# 5. Typing & Validation

## 5.1 Type Hints

All production code should use:

* Python type hints

---

## 5.2 Validation

Use:

* Pydantic models
* dataclasses where appropriate

Validate:

* config files
* downloaded data
* scanner inputs

---

# 6. Performance Rules

## 6.1 Avoid Premature Optimization

Prioritize:

* correctness
* readability
* stability

before micro-optimizations.

---

## 6.2 Batch Operations

Prefer:

* vectorized pandas operations
* batch inserts
* cached calculations

Avoid:

* row-by-row loops when unnecessary.

---

# 7. Error Handling

## 7.1 Fail Gracefully

System should:

* log failures clearly
* continue processing unaffected symbols
* avoid crashing entire scan pipeline

---

## 7.2 Defensive Data Handling

Handle safely:

* missing candles
* NaN values
* partial downloads
* symbol delistings
* benchmark mismatches

---

# 8. Scheduler Rules

## 8.1 Idempotency

Daily scans should be safely rerunnable.

Avoid duplicate:

* inserts
* alerts
* snapshots

---

# 9. Streamlit Rules

## 9.1 Dashboard Constraints

Dashboard should:

* read precomputed data only
* avoid expensive queries
* avoid heavy transformations

---

## 9.2 State Management

Keep frontend state simple.

Avoid:

* overly complex session state logic
* frontend business logic

---

# 10. Database Access Rules

## 10.1 Query Efficiency

Always:

* index timestamp columns
* index symbol columns
* index benchmark columns

---

## 10.2 ORM Usage

Use ORM lightly.

Prefer:

* explicit queries
* readable SQLAlchemy models

Avoid:

* deeply abstracted repository patterns
* excessive ORM magic

---

# 11. Charting Rules

## 11.1 Chart Philosophy

Charts should:

* load quickly
* remain visually clean
* emphasize ratios and leadership

Avoid chart clutter.

---

# 12. Config Philosophy

## 12.1 YAML-Driven Config

Configurable via YAML:

* benchmark mappings
* sectors
* scanner thresholds
* alert settings
* scheduling

Avoid hardcoded values.

---

# 13. Testing Philosophy

## 13.1 Priority Areas

Most important tests:

* ratio correctness
* ATH correctness
* 52WH correctness
* ranking consistency
* alert deduplication

---

# 14. Future-Proofing

## 14.1 Extensibility Rules

Design should allow:

* additional indicators
* additional scanners
* alternate data providers
* commodities
* custom rule engines

without major refactoring.

---

# 15. Anti-Patterns To Avoid

Avoid:

* giant god classes
* hidden global state
* circular imports
* duplicated logic
* dashboard-side calculations
* tightly coupled services
* hardcoded constants
* implicit side effects

---

# 16. AI Collaboration Workflow

## 16.1 Development Workflow

All AI-generated code must:

* follow PRD
* follow architecture document
* follow engineering guidelines

---

## 16.2 Preferred Development Style

Implement incrementally:

1. one subsystem at a time
2. validate outputs
3. test persistence
4. test scanner logic
5. integrate gradually

Avoid generating entire codebase in one prompt.

---

# 17. Recommended Development Order

```text
1. Config system
2. Database schema
3. Data downloader
4. Validation layer
5. Ratio engine
6. Indicator engine
7. ATH/52WH engine
8. Ranking engine
9. Watchlist engine
10. Alert engine
11. Dashboard
12. Charts
13. Scheduler integration
14. VPS deployment
```

---

# 18. Final Engineering Principle

Prefer:

* boring architecture
* predictable behavior
* explicit logic
* stable pipelines

over:

* clever abstractions
* unnecessary frameworks
* premature complexity
