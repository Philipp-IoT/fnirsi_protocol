# ADR-001: Use ARC42 for Architecture Documentation

**Status:** Accepted
**Date:** 2026-04-05

## Context

The project needs a structured way to capture and communicate its architecture.
Without a template, architecture documentation tends to be ad-hoc, inconsistent,
and hard to navigate for new contributors. Several lightweight templates exist
(ARC42, C4, RFC-style, plain wiki). The team wanted something well-known,
tool-agnostic, and easy to render in MkDocs.

## Decision

Use the [ARC42 template](https://arc42.org/) with its standard 12 sections,
rendered as Markdown pages under `docs/arc42/` in the existing MkDocs site.

## Consequences

- **Positive:** Standardised structure makes it clear where each type of
  architectural information belongs; well-known outside the project.
- **Positive:** Integrates with the existing MkDocs + Material + Mermaid stack
  with no additional tooling.
- **Positive:** Sections can be filled incrementally — empty placeholder files
  are valid.
- **Negative:** 12 sections may feel heavyweight for a small library; some
  sections (e.g., §10 Quality Scenarios) will remain sparse.
