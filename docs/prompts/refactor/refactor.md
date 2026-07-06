# Refactor Prompt — Safe Refactoring

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Improve code structure without changing behavior. This prompt owns **safe refactoring only** — readability and duplication reduction with no functional impact.

For bug fixes, use [bug_fix.md](../fix/bug_fix.md). For new features, use [implementation.md](../build/implementation.md).

## When to Use

- Reducing duplicated logic across modules
- Improving naming or module organization within existing boundaries
- Extracting helpers without changing public APIs
- Simplifying complex functions while preserving behavior

## Inputs

| Input | Description |
|-------|-------------|
| **Refactor target** | Files or modules to refactor |
| **Motivation** | What readability or duplication problem exists |
| **Constraints** | APIs, architecture, or behavior that must not change |
| **Test coverage** | Existing tests that must continue passing |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Refactored code** | Cleaner structure with identical behavior |
| **Behavior confirmation** | Statement that public API and logic are unchanged |
| **Test verification** | Handoff to [testing.md](../testing/testing.md) |

## Rules

- **No behavior change** — inputs and outputs must remain identical.
- **No API change** — public interfaces, imports, and function signatures preserved.
- **No architecture change** — modules stay in the same layer.
- **Reduce duplication** — extract shared logic into appropriate layers per [Dependency Rules](../../AI_CONTEXT.md#dependency-rules).
- **Improve readability** — shorter functions, clearer names, less nesting.
- **Keep tests passing** — run `pytest` before and after.

## Constraints

- Do not add features or fix bugs during refactoring.
- Do not move modules across architectural layers.
- Do not rename public APIs without explicit request.
- Do not refactor unrelated code outside the stated target.
- Follow [AI_CONTEXT.md](../../AI_CONTEXT.md) and [General Rules](../README.md#general-rules).

## Example Usage

```
Complete the Pre-Execution Checklist, then refactor.

Target: app/core/logger.py
Goal: Extract sink configuration into private helpers without changing public API.

Constraints:
- from app.core.logger import logger must remain unchanged
- No behavior change
- All tests must pass

Hand off to Testing when complete.
```
