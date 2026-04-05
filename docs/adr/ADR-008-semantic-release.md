# ADR-008: Using Semantic Release (Python-Based)

**Status:** Accepted
**Date:** 2026-04-05

## Context

Manual version management (editing `__version__`, writing changelogs,
creating git tags) is error-prone and tedious. The Conventional Commits
discipline (ADR-007) enables fully automated version calculation based on
commit types. `python-semantic-release` is the established Python-ecosystem
tool for this workflow, integrating with `hatch-vcs` for version embedding.

## Decision

Use `python-semantic-release` (≥ 9) to automate version bumping, git
tagging, and changelog generation. Releases are triggered **manually** via
the `release.yml` GitHub Actions workflow rather than on every push to
`main`. A `dry_run` mode is available for previewing the next version.
Version source is `tag` (driven by git tags); the version is embedded into
the package at build time via `hatch-vcs`.

## Consequences

- **Positive:** Eliminates manual version editing; version is always
  derived from git history.
- **Positive:** `CHANGELOG.md` is generated automatically from conventional
  commit messages.
- **Positive:** `dry_run` allows safe preview before committing a release.
- **Negative:** Requires strict adherence to Conventional Commits (ADR-007);
  a single malformed commit message can produce an incorrect version bump.
- **Negative:** Manual trigger adds a human step; could be automated further
  but was intentionally kept manual for control.
