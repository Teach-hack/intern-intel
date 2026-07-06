# InternIntel — AI Development Guide

This document is the permanent engineering specification and AI development guide for the **InternIntel** repository. All contributors and AI assistants should read this file before making architectural or implementation decisions.

---

## 1. Project Overview

### Project Name

**InternIntel**

### Purpose

InternIntel is an Internship Intelligence Platform that monitors company career pages and Applicant Tracking System (ATS) platforms to discover, store, and surface high-quality internship opportunities for students and early-career developers.

### Long-Term Vision

Build a scalable, automated internship discovery system that:

- Continuously monitors multiple hiring sources with minimal manual intervention
- Maintains a clean, deduplicated database of internship listings
- Delivers timely, relevant notifications to the right audience
- Evolves into a full internship intelligence platform with ranking, filtering, and a user-facing dashboard
- Supports a future migration from SQLite to PostgreSQL as data volume and concurrency grow

---

## 2. Main Goal

The application continuously discovers new internships from company career pages and ATS platforms, stores them in a structured database, filters duplicates, and sends notifications to users.

At a high level, the pipeline is:

1. **Discover** — Scrape or fetch listings from configured sources
2. **Normalize** — Parse raw responses into a consistent internship schema
3. **Store** — Persist listings in the database with deduplication by URL
4. **Track** — Maintain audit fields such as `first_seen`, `last_seen`, `created_at`, and `updated_at`
5. **Notify** — Alert users when new or relevant opportunities are found

The system prioritizes reliability, maintainability, and clear separation of concerns over quick, tightly coupled implementations.

---

## High-Level Architecture

The end-to-end data flow across InternIntel follows this pipeline:

```
Career Pages
    ↓
HTTP Client
    ↓
Base Scraper
    ↓
ATS Connectors + Company Scrapers
    ↓
Internship Model
    ↓
Database
    ↓
Telegram Notification
```

Each stage is implemented as a separate, reusable component. Scrapers fetch and normalize listings, the ORM model defines the storage schema, the database persists and deduplicates records, and the notification layer alerts users when new opportunities are found.

---

## 3. Target Users

InternIntel is designed for:

- **BCA students**
- **Freshers**
- **Software engineering students**
- **Entry-level developers**

The platform should surface opportunities that are relevant, timely, and easy to act on for candidates with limited industry experience.

---

## 4. Supported Sources (Planned)

The following sources are planned for integration:

| Source Type | Examples |
|-------------|----------|
| Company Career Pages | Direct company hiring sites |
| Greenhouse | ATS job boards |
| Lever | ATS job boards |
| Workday | Enterprise ATS portals |
| Ashby | Modern ATS platform |
| SmartRecruiters | ATS and recruiting platform |

Each source should be implemented as a dedicated, reusable connector or scraper following the project’s single-responsibility architecture.

---

## 5. Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.13+ |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (future PostgreSQL) |
| HTTP Client | httpx |
| HTML Parsing | BeautifulSoup |
| Browser Automation | Playwright |
| Logging | Loguru |
| Configuration | PyYAML |
| CI/CD | GitHub Actions |

Additional tooling in use or planned:

- **Black** — code formatting
- **Ruff** — linting
- **Pytest** — testing
- **Pydantic** — structured data validation where appropriate

---

## HTTP Strategy

All scraping and data retrieval must follow this priority order:

1. **httpx** — preferred for fast, lightweight HTTP requests
2. **BeautifulSoup** — parse static HTML responses
3. **JSON APIs** — use structured API endpoints when available
4. **Playwright** — only when necessary

**Playwright should be used only when static HTTP requests cannot retrieve the required information.** This typically applies to JavaScript-rendered career pages or ATS portals that do not expose usable HTML or JSON over a standard HTTP response.

Default to httpx and BeautifulSoup first. Escalate to Playwright only after confirming that simpler methods are insufficient.

---

## 6. Architecture Rules

All implementation must follow these architectural constraints.

### Layering and Responsibility

| Directory | Responsibility |
|-----------|----------------|
| `app/core/` | Shared infrastructure (config loader, logger, base abstractions) |
| `app/database/` | SQLAlchemy engine, session management, declarative base |
| `app/models/` | ORM models only |
| `app/services/` | Business logic |
| `app/companies/` | One scraper per company |
| `app/utils/` | Reusable helper functions |
| `app/config/` | YAML configuration files |
| `app/constants/` | Shared constants and enums |
| `scripts/` | Operational scripts (e.g. database initialization) |

### Mandatory Rules

- **Keep business logic out of ORM models.** Models define schema and column behavior only.
- **No module reads YAML directly except the Config Loader.** All configuration access must go through `app.core.config.settings`.
- **No direct HTTP requests outside the HTTP Client.** All network I/O must be centralized in a dedicated HTTP client module (planned).
- **No `print()` statements.** Use the centralized logger from `app.core.logger`.
- **Use type hints everywhere.** All public functions, methods, and module-level APIs must be typed.
- **Use Google-style docstrings.** Document public modules, classes, and functions.
- **Follow the single responsibility principle.** Each module should do one thing well.
- **Prefer reusable components over duplicated code.** Extract shared logic into `core/`, `utils/`, or services.
- **Store timestamps in UTC.** All datetime fields must be timezone-aware.
- **Never silently ignore exceptions.** Log meaningful errors and re-raise when appropriate.
- **Never hardcode secrets.** Use environment variables or configuration files.
- **URL must be unique** in the internship model for deduplication.

### Current Foundation

The following infrastructure is already in place:

- `app.core.config` — singleton configuration loader with dot-notation access
- `app.core.logger` — centralized Loguru logger with console and rotating file output
- `app.database` — SQLAlchemy engine, session factory, and `get_session()` context manager
- `app.models.internship` — `Internship` ORM model
- `scripts/create_database.py` — database table initialization script

---

## Current Project Structure

The repository is organized as follows:

```
intern-intel/
├── app/
│   ├── companies/          # One scraper per company (planned)
│   ├── config/             # YAML configuration files
│   │   ├── companies.yaml
│   │   ├── keywords.yaml
│   │   └── settings.yaml
│   ├── constants/          # Shared constants and enums
│   ├── core/               # Config loader, logger, shared abstractions
│   │   ├── config.py
│   │   └── logger.py
│   ├── database/           # SQLAlchemy engine, session, base
│   │   ├── base.py
│   │   ├── database.py
│   │   └── session.py
│   ├── models/             # ORM models
│   │   └── internship.py
│   ├── services/           # Business logic (planned)
│   └── utils/              # Reusable helper functions
├── data/
│   └── database/           # SQLite database storage
├── docs/                   # Project documentation
├── logs/                   # Application log files
├── scripts/
│   └── create_database.py  # Database initialization script
├── tests/                  # Pytest test suite
├── main.py                 # Application entry point
├── README.md
└── requirements.txt
```

---

## Dependency Rules

Dependencies must flow upward through the application layers. Lower layers must never depend on higher layers.

```
app/core
    ↑
app/database
    ↑
app/models
    ↑
app/services
    ↑
app/companies
```

### Allowed Import Direction

| Layer | May Import From |
|-------|-----------------|
| `app/core` | Standard library, third-party libraries only |
| `app/database` | `app/core` |
| `app/models` | `app/database` (Base), `app/core` |
| `app/services` | `app/models`, `app/database`, `app/core`, `app/utils`, `app/constants` |
| `app/companies` | `app/services`, HTTP client (planned), `app/core`, `app/utils`, `app/constants` |
| `app/utils` | Dependency-light modules only — avoid importing services or scrapers |

### Prohibited Dependencies

- `core` must not import services
- `core` must not import company scrapers
- `database` must not import services
- `models` must not import services

### Additional Rules

- **Services may import models and database.**
- **Company scrapers may import services and the HTTP client.**
- **Utilities should remain dependency-light** and must not create upward dependencies.
- **Circular imports are prohibited.** If a dependency cycle appears, refactor responsibilities before adding code.

---

## Design Philosophy

InternIntel is built as a long-term, production-quality system. All design decisions should reflect the following priorities:

- **Maintainability over shortcuts**
- **Readability over clever code**
- **Reusable components over duplicated logic**
- **Explicit behavior over implicit behavior**
- **Composition over inheritance**
- **Small focused modules**
- **Long-term scalability**
- **Testability**
- **Clean architecture**

When trade-offs arise, favor the option that is easier to understand, test, and extend in six months — not the option that is fastest to write today.

---

## 7. Coding Standards

### Formatting and Linting

- **Black** for consistent code formatting
- **Ruff** for linting — all checks must pass before committing

### Testing

- **Pytest** for unit and integration tests
- Every important module should have meaningful test coverage
- Avoid tests that only assert trivial or obvious behavior

### Python and SQLAlchemy

- **SQLAlchemy 2.x only** — use `Mapped[]`, `mapped_column()`, and `DeclarativeBase`
- **Pathlib instead of `os.path`** for all filesystem operations
- **No hardcoded values** — paths, timeouts, log levels, and feature flags come from configuration
- **Configuration must come from the Config Loader** (`settings.get("key.subkey")`)

### Git Conventions

One feature per commit. Use conventional commit messages:

```
feat(database): create internship model
fix(scraper): handle empty response
refactor(core): improve parser
```

### Code Quality

- Use descriptive names
- Avoid magic numbers
- Keep files small and focused
- Write docstrings for public methods
- Prefer composition over inheritance

---

## Performance Guidelines

Performance optimizations should be deliberate and measured. Apply the following guidelines across the codebase:

- **Reuse HTTP sessions** — avoid creating a new client or session per request
- **Avoid unnecessary database queries** — fetch only what is needed
- **Batch database writes whenever possible** — reduce round-trips during scrape runs
- **Cache immutable configuration** — rely on the Config Loader singleton; do not re-read YAML in other modules
- **Avoid repeated filesystem reads** — load static resources once and reuse them
- **Prefer lazy initialization for expensive resources** — defer browser and network setup until required
- **Avoid unnecessary browser automation** — prefer lightweight HTTP and HTML parsing first
- **Use Playwright only when static HTML is insufficient** — reserve browser automation for JavaScript-rendered pages

Premature optimization is discouraged. Readability and correctness come first unless a measured bottleneck exists.

---

## 8. Development Workflow

All changes should follow this workflow:

```
Architecture
    ↓
Cursor Implementation
    ↓
Code Review
    ↓
black .
    ↓
ruff check .
    ↓
pytest
    ↓
Git Commit
```

### Step Details

1. **Architecture** — Confirm the change fits the existing layering and does not introduce coupling or duplicated logic.
2. **Cursor Implementation** — Implement the smallest correct change using existing patterns.
3. **Code Review** — Verify architecture rules, typing, docstrings, and error handling.
4. **`black .`** — Format all Python files.
5. **`ruff check .`** — Resolve all lint errors.
6. **`pytest`** — Ensure tests pass.
7. **Git Commit** — Commit with a clear, conventional message.

### Local Commands

```bash
black .
ruff check .
pytest
PYTHONPATH=. python scripts/create_database.py
```

---

## Quality Gate

Every implementation must satisfy all of the following before it is considered complete:

- ✓ Black formatting
- ✓ Ruff linting
- ✓ Pytest
- ✓ Type hints
- ✓ Google-style docstrings
- ✓ Architecture rules
- ✓ Configuration through Config Loader
- ✓ Centralized logging

**No implementation is complete until every quality gate passes.**

---

## Error Handling Policy

Consistent error handling is required across all modules:

- **Never silently ignore exceptions**
- **Log meaningful context** using the centralized logger from `app.core.logger`
- **Re-raise unexpected exceptions** after logging when the caller must handle failure
- **Use explicit exceptions** with clear, actionable messages
- **Validate external inputs** from scrapers, APIs, and configuration before use
- **Fail fast on invalid configuration** — do not proceed with missing or malformed settings

---

## Definition of Done

A task is complete only if all of the following are true:

- Code builds successfully
- `black .` passes
- `ruff check .` passes
- `pytest` passes
- Documentation is updated when needed
- Architecture remains consistent with this specification
- Commit is ready
- No `TODO` comments remain unless explicitly approved

---

## 9. Future Roadmap

The following modules and capabilities are planned:

| Module | Description |
|--------|-------------|
| **HTTP Client** | Centralized async/sync HTTP layer using httpx with retries, timeouts, and user-agent configuration |
| **Base Scraper** | Abstract scraper interface shared by all source implementations |
| **ATS Connectors** | Dedicated connectors for Greenhouse, Lever, Workday, Ashby, and SmartRecruiters |
| **Company Scrapers** | Per-company scrapers under `app/companies/` |
| **Telegram Notifications** | Alert users when new internships are discovered |
| **GitHub Actions** | Automated scraping, testing, and deployment pipelines |
| **AI Ranking** | Score and rank internships by relevance to user profiles |
| **Dashboard** | Web interface for browsing, filtering, and managing listings |

### Database Evolution

- **Current:** SQLite at `data/database/internships.db`
- **Future:** PostgreSQL for production-scale storage and concurrency

### Configuration Evolution

- **Current:** YAML-based settings via `app/config/settings.yaml`
- **Future:** Optional `.env` support for secrets and environment-specific overrides

---

## Engineering Principles

InternIntel should evolve as a production-quality software project. The following engineering principles guide long-term development:

- **Modular architecture** — clear boundaries between layers and responsibilities
- **High cohesion** — related logic lives together within a module
- **Low coupling** — modules depend only on stable, lower-level abstractions
- **Dependency Injection where appropriate** — pass dependencies explicitly rather than hard-wiring them
- **SOLID principles** — especially single responsibility and dependency inversion
- **DRY** — do not repeat business logic across scrapers or services
- **KISS** — prefer simple, direct solutions over complex frameworks
- **Prefer composition over inheritance** — build behavior from small, composable parts
- **Keep public APIs stable** — avoid breaking imports and interfaces without approval
- **Favor readability over premature optimization** — optimize only when justified by evidence

---

## AI Constraints

AI assistants working in this repository must follow these constraints:

### Must NOT

- Perform unrelated refactoring
- Introduce unnecessary abstractions
- Rename public APIs without an explicit request
- Change architecture without approval
- Duplicate existing utilities
- Create multiple implementations for the same responsibility
- Introduce hidden magic behavior
- Hardcode configuration values

### Must Always

- Analyze the existing architecture before writing code
- Read this document and the relevant source files before making changes
- Follow the Dependency Rules and Quality Gate defined in this specification
- Implement the smallest correct change that satisfies the request

---

## Quick Reference for AI Assistants

When implementing changes in this repository:

1. Read this file and the existing code in the target layer before writing anything.
2. Do not create new folders, files, or patterns unless explicitly requested.
3. Reuse `settings`, `logger`, `engine`, `get_session()`, and `Base` from existing modules.
4. Keep ORM models schema-only; put business logic in services.
5. Satisfy every item in the **Quality Gate** and **Definition of Done** before considering work complete.
6. Preserve the public API unless a change is explicitly requested.

---

*Last updated: July 2026*

## Specification Version

Version: 1.0.0

Status: Stable

This document should only be modified for architectural changes.
Implementation details belong in code or module-specific documentation.