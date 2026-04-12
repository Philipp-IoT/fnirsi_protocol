# ADR-004: Using Git for Version Control

**Status:** Accepted
**Date:** 2026-04-05

## Context

The project needs version control to track changes to source code,
protocol specifications, documentation, and test artefacts. Git is the
de-facto standard for open-source Python projects and is required by the
chosen hosting platform (GitHub).

## Decision

Use Git for all version control. The repository is a single monorepo
containing the Python library, protocol specification (`.ksy`),
generated parser, documentation, and CI configuration.

## Consequences

- **Positive:** Universal tooling support; all contributors can be expected
  to know Git.
- **Positive:** Full history including binary captures (pcapng are
  `.gitignore`d; hex dumps are committed).
- **Negative:** Git is not ideal for large binary files; raw `.pcapng`
  captures are therefore excluded from version control.
