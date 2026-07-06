# Review Prompt — Code Review

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Review completed **code** against architecture rules and the quality gate. This prompt owns **code review only** — report findings, do not fix or implement.

For specification documents, use [specification_review.md](specification_review.md).

## When to Use

- After implementation and before the quality gate
- When reviewing a pull request or local code changes
- After a fix prompt resolves a bug or lint error

## Inputs

| Input | Description |
|-------|-------------|
| **Changed files** | Files created or modified |
| **Original request** | What the implementation was supposed to achieve |
| **Specification** | Relevant `docs/specifications/` document if applicable |
| **Review focus** | Architecture, security, performance, or completeness |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Compliance summary** | Pass or fail against architecture and dependency rules |
| **Issue list** | Findings categorized by severity with explanation |
| **Quality gate status** | Pass or fail per [Quality Gate](../../AI_CONTEXT.md#quality-gate) |
| **Approval status** | Ready for quality gate, needs fixes, or needs replanning |

### Severity Levels

Every finding must include a severity and a short explanation.

| Severity | Meaning |
|----------|---------|
| **Critical** | Blocks merge — architecture violation, data loss risk, security flaw, or broken public API |
| **High** | Must fix before commit — missing error handling, dependency violation, or quality gate failure |
| **Medium** | Should fix — incomplete typing, weak test coverage, or inconsistent patterns |
| **Low** | Minor issue — naming, documentation gaps, or non-blocking style concerns |
| **Suggestion** | Optional improvement — no action required |

### Finding Format

Each finding must state:

1. **Severity**
2. **File or module**
3. **Issue**
4. **Explanation** — why it matters
5. **Recommended action**

## Rules

- Review code only — do not rewrite unless explicitly asked.
- Check against [AI_CONTEXT.md](../../AI_CONTEXT.md): architecture, dependencies, quality gate.
- Do not approve work that violates dependency rules.
- Hand off fixes to the [Fix prompt](../fix/bug_fix.md).

## Constraints

- Do not implement fixes during review.
- Do not review specification documents — use [specification_review.md](specification_review.md).
- Do not treat style preferences as blockers unless Ruff flags them.

## Example Usage

```
Complete the Pre-Execution Checklist, then review.

Changed files:
- app/core/http_client.py
- tests/test_http_client.py

Specification: docs/specifications/http_client.md

Report findings by severity (Critical / High / Medium / Low / Suggestion).
Include explanation for every finding.
Do not modify code.
```
