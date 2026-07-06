# Planning Prompt — Architecture and Scope Analysis

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Produce an architecture and dependency analysis before any code or specification is written. This prompt owns **planning only** — architecture fit, dependency mapping, and implementation order.

## When to Use

- Starting a new feature or module
- Assessing which layer a component belongs in
- Determining whether a specification document is required first
- Evaluating impact on existing modules

## Inputs

| Input | Description |
|-------|-------------|
| **Feature description** | What needs to be built and why |
| **Affected layers** | Directories likely touched (`core`, `database`, `models`, `services`, `companies`) |
| **Dependencies** | Known upstream or downstream modules |
| **Constraints** | Scope, compatibility, or timeline limits |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Architecture fit assessment** | Whether the change belongs in the proposed layer |
| **Dependency map** | Allowed and prohibited imports per [Dependency Rules](../../AI_CONTEXT.md#dependency-rules) |
| **File plan** | New or modified files with single-responsibility justification |
| **Configuration needs** | New `settings.yaml` keys required, if any |
| **Specification recommendation** | Whether a `docs/specifications/` document is needed — hand off to [Documentation prompt](../documentation/write_documentation.md) |
| **Risk summary** | Circular imports, coupling, or scope creep risks |
| **Implementation order** | Recommended sequence of build steps |

## Rules

- Planning covers architecture, dependencies, and order — not specification writing or code.
- Respect dependency direction: `core` → `database` → `models` → `services` → `companies`.
- Identify reusable infrastructure (`settings`, `logger`, `engine`, `get_session()`, `Base`) before proposing new modules.
- Prefer extending existing patterns over new abstractions.
- Flag configuration needs; do not define specification content here.

## Constraints

- Do not write implementation code.
- Do not write specification documents — recommend them and defer to the Documentation prompt.
- Do not create files or folders.
- Do not propose architecture changes without stating reason and impact.
- Output must be implementation-independent.

## Example Usage

```
Complete the Pre-Execution Checklist, then plan the following.

Feature: Base Scraper abstract class for company scrapers and ATS connectors.

Deliver:
- Architecture fit assessment (target layer)
- Dependency map
- File plan
- Whether docs/specifications/ is needed first
- Implementation order

Do not write code or specifications.
```
