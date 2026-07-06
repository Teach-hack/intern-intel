# Documentation Prompt — Specifications and Guides

> Complete the [Pre-Execution Checklist](../README.md#pre-execution-checklist) before proceeding.

## Purpose

Write and improve engineering documentation. This prompt owns **documentation only** — specifications, guides, and README content.

Architecture planning belongs in [architecture_planning.md](../planning/architecture_planning.md). Code belongs in [implementation.md](../build/implementation.md).

## When to Use

- Creating a module specification under `docs/specifications/`
- Writing guides or README content
- Updating `docs/AI_CONTEXT.md` for architectural changes
- Improving existing documentation without rewriting established content

## Inputs

| Input | Description |
|-------|-------------|
| **Document type** | Specification, guide, README, or context update |
| **Target file** | Path under `docs/` |
| **Module scope** | What the document covers |
| **Required sections** | Sections that must be included |
| **Existing documents** | Related specs or guides for consistency |

## Expected Outputs

| Output | Description |
|--------|-------------|
| **Complete Markdown document** | Professional, readable engineering documentation |
| **Consistent formatting** | Matches existing InternIntel documentation style |
| **Implementation-independent content** | Design contracts without source code |
| **Cross-references** | Links to `AI_CONTEXT.md` and related specifications |
| **Metadata block** | For new specifications — see below |

## Specification Metadata

New documents under `docs/specifications/` should include a metadata block at the top:

| Field | Description |
|-------|-------------|
| **Version** | Semantic version of the specification (e.g. `1.0.0`) |
| **Status** | `Draft`, `Review`, `Stable`, or `Deprecated` |
| **Owner** | Module or team responsible for maintenance |
| **Last Updated** | Date of last meaningful change |

This is guidance for future specifications only. Do not modify existing specification files to add metadata unless explicitly requested.

## Rules

- Preserve existing sections when improving — add, do not rewrite.
- Keep specifications implementation-independent — no source code.
- Align with [AI_CONTEXT.md](../../AI_CONTEXT.md) for architecture and quality rules.
- Cross-reference instead of duplicating content across documents.
- Hand off completed specifications to [specification_review.md](../review/specification_review.md).

## Constraints

- Do not modify source code.
- Do not remove existing documentation content.
- Do not use emojis.
- Do not change `AI_CONTEXT.md` unless documenting an architectural change.

## Example Usage

```
Complete the Pre-Execution Checklist, then write.

Create: docs/specifications/base_scraper.md

Include metadata (Version, Status, Owner, Last Updated).
Include: purpose, responsibilities, non-responsibilities, public API, configuration.
Cross-reference AI_CONTEXT.md.

Do not write implementation code.
Hand off to specification_review.md when complete.
```
