# ADR-006: Using GitHub Actions for CI Verification

**Status:** Accepted
**Date:** 2026-04-05

## Context

Automated CI is needed to catch regressions in linting, type checking,
and unit tests on every pull request and push to `main`. GitHub Actions
is available without additional cost given the choice of GitHub hosting
(ADR-005) and requires no external service configuration.

## Decision

Use GitHub Actions for all CI pipelines: lint (`ruff`), type check
(`mypy`), unit tests (`pytest`), and documentation build (`mkdocs build`).
A separate `release.yml` workflow handles manual release triggering.

## Consequences

- **Positive:** CI runs automatically on PRs with no additional service
  accounts or tokens.
- **Positive:** Workflow YAML lives in the repository alongside the code
  it tests, keeping CI and code in sync.
- **Negative:** Real-hardware integration tests (requiring a physical
  DPS-150) cannot run in CI and are excluded.
- **Negative:** Further vendor coupling to GitHub (see ADR-005).
