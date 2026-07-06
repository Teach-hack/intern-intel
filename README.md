# InternIntel - Project Rules

## Goal

Build a scalable Internship Intelligence Platform that monitors company career pages and delivers high-quality internship opportunities.

---

## General Rules

- Write clean and readable code.
- Follow SOLID principles wherever practical.
- Never duplicate business logic.
- Keep functions short and focused.
- Prefer composition over inheritance.
- Every module should have a single responsibility.

---

## Python Rules

- Python 3.13+
- Use type hints everywhere.
- Use dataclasses or Pydantic where appropriate.
- Use pathlib instead of os.path whenever possible.
- No global mutable variables.
- Never hardcode secrets.

---

## Folder Rules

companies/
One scraper per company.

core/
Shared engine and abstract classes.

models/
Database models.

services/
Business logic.

utils/
Helper functions.

config/
Configuration loader.

---

## Database

- SQLAlchemy ORM only.
- Never write raw SQL unless absolutely necessary.
- URL must be unique.
- Store timestamps in UTC.

---

## Logging

Use Loguru.

Never use print() in production code.

---

## Configuration

All configuration must come from:

.env

or

YAML files

No hardcoded values.

---

## Error Handling

Never silently ignore exceptions.

Log meaningful errors.

---

## Git Rules

One feature = one commit.

Commit message examples:

feat(database): create internship model

fix(scraper): handle empty response

refactor(core): improve parser

---

## Testing

Every important module should have tests.

---

## Code Quality

Use descriptive names.

Avoid magic numbers.

Write docstrings for public methods.

Keep files small.
