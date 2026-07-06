# Review Prompt — Specification Review

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Review engineering documentation for completeness and consistency. This prompt owns **specification review only** — verify documents, do not write code.

For code changes, use [code_review.md](code_review.md).

## When to Use

- After creating or updating a `docs/specifications/` document
- Before implementation begins on a new module
- When improving existing documentation
- Verifying a specification aligns with `AI_CONTEXT.md`

## Inputs

| Input | Description |
|-------|-------------|
| **Document path** | Specification or guide under review |
| **Document type** | Specification, guide, README, or context update |
| **Related specs** | Other documents that should be consistent |
| **Review focus** | Completeness, architecture, or cross-references |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Completeness assessment** | Required sections present or missing |
| **Consistency findings** | Conflicts with `AI_CONTEXT.md` or other specs |
| **Issue list** | Findings by severity with explanation |
| **Approval status** | Ready for implementation, needs revision, or needs replanning |

### Severity Levels

| Severity | Meaning |
|----------|---------|
| **Critical** | Missing public API, responsibilities, or architecture conflict |
| **High** | Missing configuration, error handling, or dependency rules |
| **Medium** | Incomplete sections, weak cross-references, or unclear constraints |
| **Low** | Formatting, wording, or minor structural issues |
| **Suggestion** | Optional improvements |

Every finding must include a short explanation.

## Rules

Verify the document against:

| Check | Question |
|-------|----------|
| **Completeness** | Are purpose, responsibilities, and non-responsibilities defined? |
| **Consistency** | Does it align with [AI_CONTEXT.md](../../AI_CONTEXT.md)? |
| **Architecture alignment** | Correct layer, dependencies, and constraints? |
| **Implementation independence** | No source code or framework coupling? |
| **Cross-references** | Links to `AI_CONTEXT.md` and related specifications? |
| **Missing sections** | Public API, configuration, error handling, testing strategy? |
| **Metadata** | Version, Status, Owner, Last Updated present for new specs? |

## Constraints

- Do not generate implementation code.
- Do not rewrite the document — report findings only unless asked to fix.
- Do not review application code — use [code_review.md](code_review.md).
- Hand off documentation fixes to [write_documentation.md](../documentation/write_documentation.md).

## Example Usage

```
Complete the Pre-Execution Checklist, then review.

Document: docs/specifications/http_client.md

Verify:
- Completeness and consistency with AI_CONTEXT.md
- Architecture alignment and implementation independence
- Cross-references and missing sections

Report findings by severity with explanation.
Do not generate implementation code.
```
