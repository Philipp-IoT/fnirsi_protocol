# ADR-007: Using Conventional Commits

**Status:** Accepted
**Date:** 2026-04-05

## Context

The project uses automated semantic versioning (see ADR-008), which requires
a machine-parseable commit message format. Additionally, a consistent commit
style improves the readability of `git log` and auto-generated changelogs.
The [Conventional Commits](https://www.conventionalcommits.org/) specification
is the industry-standard format supported by `python-semantic-release`.

## Decision

All commits must follow the Conventional Commits specification:
`<type>[optional scope]: <description>`. Accepted types and their version
bump effects are documented in [Contributing](../dev/contributing.md).

## Consequences

- **Positive:** Enables fully automated versioning and changelog generation
  (ADR-008).
- **Positive:** Commit history is self-documenting; the type prefix makes
  the nature of each change immediately clear.
- **Negative:** Adds a formatting discipline requirement; contributors must
  learn the convention.
- **Negative:** No automated enforcement (no commit-msg hook) is currently
  configured; compliance relies on author discipline and PR review.
