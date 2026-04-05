# ADR-003: Vibe-Coding Using Claude Code

**Status:** Accepted
**Date:** 2026-04-05

## Context

The project is developed by a single engineer. AI-assisted development
(colloquially "vibe-coding") can significantly accelerate implementation of
boilerplate, tests, documentation scaffolding, and refactoring. Claude Code
(Anthropic's CLI AI assistant) is used as the primary AI coding tool.
The question is whether to acknowledge this openly or treat it as an
implementation detail.

## Decision

AI-assisted development using Claude Code is an accepted and openly documented
part of the development workflow. Contributions generated or substantially
shaped by AI are committed without special marking beyond what conventional
commits already provide. Human review and sign-off is always required before
committing AI-generated code.

## Consequences

- **Positive:** Increased development velocity for boilerplate, tests, and
  documentation scaffolding.
- **Positive:** Transparent acknowledgement avoids misrepresentation of effort.
- **Negative:** AI-generated code may require careful review to avoid
  subtle bugs or stylistic drift.
- **Constraint:** Architecture documentation content remains human-authored
  per ADR-002, regardless of this decision.
