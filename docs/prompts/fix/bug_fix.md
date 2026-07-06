# Fix Prompt — Bug Fix and Remediation

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Resolve bugs, test failures, and review findings with the smallest correct fix. This prompt owns **remediation only**.

## When to Use

- Fixing runtime bugs or incorrect behavior
- Resolving test failures
- Addressing code review findings
- Resolving Ruff or Black failures

## Inputs

| Input | Description |
|-------|-------------|
| **Problem description** | What is broken or failing |
| **Error output** | Stack traces, lint messages, or test failure output |
| **Affected files** | Files likely involved |
| **Review findings** | Severity-tagged items from [code_review.md](../review/code_review.md) |
| **Constraints** | APIs, architecture, or modules that must not change |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Root cause** | Brief explanation of why the issue occurred |
| **Minimal fix** | Smallest change that resolves the problem |
| **Verification** | Handoff to [Testing](../testing/testing.md) and [Workflow](../workflow/development_cycle.md) prompts |

## Bug Priority

Address issues in this order when multiple failures exist:

| Priority | Category |
|----------|----------|
| **1** | Runtime bugs |
| **2** | Data corruption |
| **3** | Security |
| **4** | Test failures |
| **5** | Ruff |
| **6** | Black |

## Rules

- Fix only what is necessary to resolve the reported issue.
- Preserve architecture, public APIs, and function names per [AI_CONTEXT.md](../../AI_CONTEXT.md).
- Log exceptions through `app.core.logger`.
- Do not introduce unrelated refactoring — use the [Refactor prompt](../refactor/refactor.md) instead.

## Constraints

- Do not rename public APIs unless the fix explicitly requires it.
- Do not change architecture to work around a bug.
- Do not modify files outside the issue scope unless a dependency demands it.
- Do not use `print()` — use the centralized logger.

## Example Usage

```
Complete the Pre-Execution Checklist, then fix.

Priority 5 — Ruff errors in app/core/logger.py and app/database/session.py.

Constraints:
- Keep public API: from app.core.logger import logger
- Preserve session rollback and re-raise behavior

Fix highest priority issues first.
Hand off to Testing when complete.
```
