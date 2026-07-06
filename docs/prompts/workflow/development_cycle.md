# Workflow Prompt — Full Development Cycle

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Orchestrate the complete development cycle and confirm commit readiness. This prompt owns **orchestration only** — it coordinates other prompts without replacing them.

## When to Use

- Final verification before creating a git commit
- Confirming definition of done after implementation
- Running the end-to-end cycle for a feature or fix

## Inputs

| Input | Description |
|-------|-------------|
| **Task summary** | What was built or changed |
| **Changed files** | Complete list of created or modified files |
| **Specification** | Applicable `docs/specifications/` document |
| **Prior phase outputs** | Planning, review, fix, and testing results |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Phase confirmation** | Each workflow phase completed or skipped with reason |
| **Quality gate report** | Pass or fail per [Quality Gate](../../AI_CONTEXT.md#quality-gate) |
| **Commit readiness** | Whether [Definition of Done](../../AI_CONTEXT.md#definition-of-done) is met |
| **Suggested commit message** | Conventional commit message if ready |
| **Remediation recommendation** | Next prompt if quality gate fails |

## Rules

### Primary Flow

```
Planning          → architecture_planning.md
    ↓
Specification     → write_documentation.md (if new module)
    ↓
Implementation    → implementation.md
    ↓
Review            → code_review.md
    ↓
Fix               → bug_fix.md (if needed)
    ↓
Testing           → testing.md
    ↓
Quality Gate
    ↓
Commit
```

### Remediation Flow

If **any** quality gate item fails, do not commit. Return to:

```
Review
    ↓
Fix
    ↓
Testing
    ↓
Quality Gate
    ↓
Commit
```

Repeat until every quality gate item passes or the task requires replanning.

### Phase Delegation

| Phase | Delegated To |
|-------|--------------|
| Planning | [architecture_planning.md](../planning/architecture_planning.md) |
| Specification | [write_documentation.md](../documentation/write_documentation.md) |
| Implementation | [implementation.md](../build/implementation.md) |
| Review | [code_review.md](../review/code_review.md) |
| Fix | [bug_fix.md](../fix/bug_fix.md) |
| Testing | [testing.md](../testing/testing.md) |
| Quality Gate | [AI_CONTEXT.md — Quality Gate](../../AI_CONTEXT.md#quality-gate) |
| Definition of Done | [AI_CONTEXT.md — Definition of Done](../../AI_CONTEXT.md#definition-of-done) |

### Verification Commands

```bash
black .
ruff check .
pytest
```

## Constraints

- Do not implement, review, or fix — delegate to the appropriate prompt.
- Do not commit or push unless explicitly requested.
- One feature per commit with a conventional message.
- Do not skip remediation when quality gate fails.

## Example Usage

```
Complete the Pre-Execution Checklist, then orchestrate.

Task: HTTP Client implementation complete.
Files: app/core/http_client.py, tests/test_http_client.py

Confirm all phases complete.
Run quality gate.
If any item fails, recommend Review → Fix → Testing → Quality Gate.
Report commit readiness and suggest a commit message.
Do not create the commit unless I ask.
```
