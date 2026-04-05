# ADR-002: Architecture Documentation is Human-Authored

**Status:** Accepted
**Date:** 2026-04-05

## Context

AI coding assistants (including Claude Code) can generate plausible-sounding
architecture documentation quickly. However, auto-generated architecture docs
risk being shallow, inaccurate, or disconnected from actual design intent.
Architecture documentation is most valuable when it reflects deliberate,
human-reasoned decisions.

## Decision

All content in `docs/arc42/` is human-authored. AI tools may scaffold structure
(file layout, section headings, placeholder text) but must not generate the
substantive content of any ARC42 section. Placeholder text explicitly marks
sections as unfilled (`_To be filled._`).

## Consequences

- **Positive:** Documentation accurately reflects actual architectural intent
  and hard-won knowledge.
- **Positive:** Forces the author to think through decisions rather than
  accepting plausible-but-wrong AI output.
- **Negative:** Documentation will be written more slowly and may remain
  incomplete for longer than if AI-generated.
- **Note:** This decision applies only to architecture documentation, not to
  code. See ADR-003 for the code authoring approach.
