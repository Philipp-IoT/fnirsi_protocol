# 2. Architecture Constraints

## Technical Constraints

| Constraint | Description |
| --- | --- |
| USB CDC serial interface | The FNIRSI DPS-150 communicates via USB CDC ACM (VID `0x2e3c` / PID `0x5740`) at 9600 baud, 8N1. Control signals must be DTR=off, RTS=on. This is a fixed hardware constraint. |
| Proprietary binary protocol | The wire protocol is undocumented by the manufacturer; all knowledge is derived from reverse engineering USB captures. Protocol gaps remain (e.g., status blob tail layout). |
| Python ≥ 3.11 | All code targets Python 3.11+. CI tests against 3.11 and 3.12. |
| Libraries over reinvention | Prefer established libraries (pyserial, Typer, Rich, Kaitai Struct) over custom implementations. |
| Kaitai Struct as protocol source of truth | The protocol wire format is formally defined in `fnirsi_dps150.ksy`. Code and documentation are derived from this single source. |
| IEEE 754 little-endian floats | All voltage and current values on the wire use 32-bit IEEE 754 floats in little-endian byte order. This is dictated by the device firmware. |
| No hardware-in-the-loop CI | A physical DPS-150 is not available in CI. Integration tests require manual verification against real hardware. |

## Organisational Constraints

| Constraint | Description |
| --- | --- |
| MIT license | The project is released under the MIT license, including the protocol specification ([ADR-005](../adr/ADR-005-github-hosting.md)). |
| Single developer | Side project by Philipp Bolte; no external contributors expected. |
| No fixed schedule | Development started April 2026, driven by interest and availability without deadlines. |
| AI-assisted coding with human review | Code may be generated with AI assistance (Claude Code), but all commits require human review ([ADR-003](../adr/ADR-003-vibe-coding-claude-code.md)). |
| Human-authored architecture docs | ARC42 documentation is written by hand; AI must not generate substantive architecture content ([ADR-002](../adr/ADR-002-human-authored-docs.md)). |
| GitHub platform | Source code, CI/CD, and documentation hosting are on GitHub. Migration would require reconfiguring Actions and Pages ([ADR-005](../adr/ADR-005-github-hosting.md)). |

## Conventions

| Convention | Description |
| --- | --- |
| Conventional Commits | All commit messages follow the Conventional Commits specification (`feat:`, `fix:`, `docs:`, etc.) to enable automated versioning ([ADR-007](../adr/ADR-007-conventional-commits.md)). |
| Semantic Versioning | Versions are derived exclusively from git tags via `hatch-vcs` and bumped automatically by `python-semantic-release` ([ADR-008](../adr/ADR-008-semantic-release.md)). |
| `uv` for environment management | All dependency and environment management uses `uv`. Plain `pip`, `venv`, or `poetry` are not used. |
| Ruff for formatting and linting | Code style is enforced by Ruff (line length 100, double quotes, target py311). |
| Strict mypy | Static type checking runs in strict mode across `src/`. |
| ARC42 documentation structure | Architecture documentation follows the ARC42 template with 12 sections ([ADR-001](../adr/ADR-001-use-arc42.md)). |
| MkDocs + Material for docs site | Documentation is built with MkDocs Material and auto-deployed to GitHub Pages on push to `main` ([ADR-006](../adr/ADR-006-github-actions-ci.md)). |
| Git version control | Single monorepo managed with Git ([ADR-004](../adr/ADR-004-git-version-control.md)). |
