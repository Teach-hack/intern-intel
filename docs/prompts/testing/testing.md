# Testing Prompt — Test Strategy and Verification

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Write and verify tests for InternIntel modules. This prompt owns **testing only** — unit, integration, regression, and quality verification.

Implementation belongs in [implementation.md](../build/implementation.md). Fixes belong in [bug_fix.md](../fix/bug_fix.md).

## When to Use

- Adding tests for new modules or behavior
- Verifying implementation against a specification
- Writing regression tests after a bug fix
- Confirming quality gate test requirements before commit

## Inputs

| Input | Description |
|-------|-------------|
| **Target module** | Code under test |
| **Specification** | Relevant `docs/specifications/` document if applicable |
| **Behavior to verify** | Expected outcomes and edge cases |
| **Test type** | Unit, integration, or regression |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Test cases** | Pytest tests covering important behavior |
| **Mock strategy** | What is mocked and why |
| **Coverage summary** | What behavior is verified |
| **Verification result** | `pytest` pass or fail report |
| **Handoff** | Ready for [Workflow](../workflow/development_cycle.md) quality gate |

## Rules

### Unit Testing

- Test one module or function in isolation.
- Mock external dependencies: network, database, filesystem.
- Cover success paths, failure paths, and boundary conditions.
- Avoid trivial assertions that only restate the implementation.

### Integration Testing

- Verify interaction between layers (e.g. service + database session).
- Use test databases or fixtures — never production data.
- Keep scope minimal and focused.

### Regression Testing

- Add a test that reproduces every fixed bug before applying the fix.
- Ensure the test fails before the fix and passes after.

### Mocking

- Mock all outbound HTTP calls — no live requests to external websites.
- Mock configuration when testing modules that read `settings`.
- Prefer dependency injection over patching globals.

### Edge Cases

- Empty inputs, missing configuration, invalid URLs
- Timeout and retry exhaustion where applicable
- Invalid or malformed external responses

### Quality Verification

```bash
pytest
black .
ruff check .
```

## Constraints

- Do not implement features — test existing or concurrently built code only.
- Do not make live network requests in tests.
- Do not skip tests for important behavior described in specifications.
- Follow [AI_CONTEXT.md](../../AI_CONTEXT.md) testing guidance.

## Example Usage

```
Complete the Pre-Execution Checklist, then test.

Target: app/core/http_client.py
Specification: docs/specifications/http_client.md

Write unit tests covering:
- successful request
- timeout
- retry and retry exhaustion
- header merging
- invalid URL
- connection failure

Mock all network calls.
Report pytest results.
Hand off to Workflow for quality gate.
```
