# Build Prompt — Implementation

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Implement the smallest correct change that satisfies the request. This prompt owns **implementation only** — writing application code per plan and specification.

## When to Use

- Building a new module after planning and specification are complete
- Extending an existing module with new functionality
- Implementing a specification from `docs/specifications/`

For tests, use the [Testing prompt](../testing/testing.md). For refactoring, use the [Refactor prompt](../refactor/refactor.md).

## Inputs

| Input | Description |
|-------|-------------|
| **Task description** | Precisely what to build or change |
| **Target files** | Files to create or modify |
| **Specification** | Link to `docs/specifications/` document if applicable |
| **Architecture plan** | Output from the planning prompt |
| **Out of scope** | What must not be changed |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Working code** | Typed, documented implementation |
| **Configuration** | New settings accessed through `settings.get()` only |
| **Handoff note** | Whether review, testing, or documentation updates are needed next |

## Task Success Criteria

A build task is complete only when:

- **Functionality works** — the requested behavior is implemented correctly
- **Architecture preserved** — correct layer, dependency direction, no business logic in models
- **Quality gate passes** — see [Quality Gate](../../AI_CONTEXT.md#quality-gate) and [General Rules](../README.md#general-rules)
- **Documentation updated when required** — specifications or guides updated if the public contract changed

Verification is performed via the [Testing](../testing/testing.md) and [Workflow](../workflow/development_cycle.md) prompts.

## Rules

- Follow [AI_CONTEXT.md](../../AI_CONTEXT.md) and [General Rules](../README.md#general-rules).
- Implement the minimum change required — no unrelated refactoring.
- Reuse `settings`, `logger`, `engine`, `get_session()`, and `Base`.
- HTTP requests only through the HTTP Client when it exists.

## Constraints

- Do not rename public APIs without explicit request.
- Do not change architecture without approval.
- Do not write tests in this prompt — use the Testing prompt.
- Do not write specifications — use the Documentation prompt.
- Do not hardcode configuration values, paths, or secrets.

## Example Usage

```
Complete the Pre-Execution Checklist, then implement.

Target: app/core/http_client.py
Specification: docs/specifications/http_client.md

Follow the public API in the specification.
Hand off to Testing and Review when complete.
Do not modify unrelated files.
```
