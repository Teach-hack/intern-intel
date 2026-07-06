# InternIntel AI Prompt Library

This library is the **standard workflow for all future development** in the InternIntel repository. Every feature, fix, and documentation change should follow the prompts defined here.

Before using any prompt, read [AI_CONTEXT.md](../AI_CONTEXT.md) — it is the permanent engineering specification for this project.

---

## Pre-Execution Checklist

Before producing any output with any prompt in this library:

1. Read [AI_CONTEXT.md](../AI_CONTEXT.md)
2. Read relevant specifications under `docs/specifications/`
3. Read existing implementation in affected modules
4. Analyze existing architecture and dependency rules

Only then proceed with the prompt.

---

## Development Workflow

All work follows this sequence:

```
Planning
    ↓
Specification
    ↓
Implementation
    ↓
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

If any quality gate item fails, return to this remediation loop before committing:

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

| Phase | Prompt | Location |
|-------|--------|----------|
| **Planning** | Architecture, dependency analysis, implementation order | [planning/architecture_planning.md](planning/architecture_planning.md) |
| **Specification** | Engineering contracts, guides, README | [documentation/write_documentation.md](documentation/write_documentation.md) |
| **Implementation** | Code implementation only | [build/implementation.md](build/implementation.md) |
| **Review** | Code and specification review | [review/](review/) |
| **Fix** | Bug and finding remediation only | [fix/bug_fix.md](fix/bug_fix.md) |
| **Refactor** | Safe refactoring without behavior change | [refactor/refactor.md](refactor/refactor.md) |
| **Testing** | Unit, integration, and regression testing | [testing/testing.md](testing/testing.md) |
| **Workflow** | End-to-end cycle orchestration | [workflow/development_cycle.md](workflow/development_cycle.md) |

---

## Development Decision Tree

Use this tree to select the correct starting prompt:

```
Need new feature?
    ↓
Planning
    ↓
Need new module?
    ↓ yes → Documentation (specification)
    ↓ no
Implementation
    ↓
Review
    ↓
Issues found?
    ↓ yes → Fix
    ↓ no
Testing
    ↓
Workflow (Quality Gate)
    ↓
Commit
```

| Situation | Start Here |
|-----------|------------|
| New feature or module | [planning/architecture_planning.md](planning/architecture_planning.md) |
| New specification needed | [documentation/write_documentation.md](documentation/write_documentation.md) |
| Write or extend code | [build/implementation.md](build/implementation.md) |
| Review code changes | [review/code_review.md](review/code_review.md) |
| Review a specification | [review/specification_review.md](review/specification_review.md) |
| Fix a bug or lint error | [fix/bug_fix.md](fix/bug_fix.md) |
| Safe refactor only | [refactor/refactor.md](refactor/refactor.md) |
| Write or extend tests | [testing/testing.md](testing/testing.md) |
| Final verification before commit | [workflow/development_cycle.md](workflow/development_cycle.md) |

---

## Prompt Index

| Folder | File | Responsibility |
|--------|------|----------------|
| `planning/` | [architecture_planning.md](planning/architecture_planning.md) | Architecture fit, dependencies, implementation order |
| `documentation/` | [write_documentation.md](documentation/write_documentation.md) | Specifications, guides, README |
| `build/` | [implementation.md](build/implementation.md) | Implementation only |
| `review/` | [code_review.md](review/code_review.md) | Code review only |
| `review/` | [specification_review.md](review/specification_review.md) | Specification review only |
| `fix/` | [bug_fix.md](fix/bug_fix.md) | Remediation only |
| `refactor/` | [refactor.md](refactor/refactor.md) | Safe refactoring only |
| `testing/` | [testing.md](testing/testing.md) | Testing strategy and verification |
| `workflow/` | [development_cycle.md](workflow/development_cycle.md) | Orchestration only |

---

## General Rules

All prompts enforce project standards defined in [AI_CONTEXT.md](../AI_CONTEXT.md):

| Standard | Reference |
|----------|-----------|
| Architecture rules | [Architecture Rules](../AI_CONTEXT.md#6-architecture-rules) |
| Dependency rules | [Dependency Rules](../AI_CONTEXT.md#dependency-rules) |
| Quality gate | [Quality Gate](../AI_CONTEXT.md#quality-gate) |
| Definition of done | [Definition of Done](../AI_CONTEXT.md#definition-of-done) |
| AI constraints | [AI Constraints](../AI_CONTEXT.md#ai-constraints) |

Individual prompts reference this section instead of repeating full rule lists.

---

## Existing Specifications

Module-specific engineering contracts live under `docs/specifications/`:

| Specification | Status |
|---------------|--------|
| [http_client.md](../specifications/http_client.md) | Design complete — implementation pending |

New specifications should include metadata fields. See [write_documentation.md](documentation/write_documentation.md).

---

## Quality Commands

```bash
black .
ruff check .
pytest
```

---

*Last updated: July 2026*
