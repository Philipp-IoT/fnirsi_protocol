# Contributing

## Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated semantic versioning.

| Prefix | Version bump | Example |
|--------|-------------|---------|
| `feat:` | Minor (0.x → patch) | `feat(protocol): add CMD 0xdb output enable` |
| `fix:` / `perf:` | Patch | `fix: correct checksum for disconnect frame` |
| `BREAKING CHANGE` | Major (0.x → minor) | `feat!: redesign device API` |
| `docs:`, `chore:`, `ci:`, `test:` | No bump | `docs: update session lifecycle` |

## Pull Request Process

1. Branch from `main`
2. Make changes (code + tests + docs if protocol-related)
3. Run locally: `uv run ruff format src tests && uv run ruff check src tests && uv run mypy && uv run pytest`
4. Open PR — CI will run lint + tests

## Release Process

Releases are **manual only** — no automatic release on push.

Trigger the `release.yml` workflow from GitHub Actions → Workflows → Release.

Use `dry_run = true` first to preview the next version without tagging.

## Protocol RE Contributions

When adding a newly reverse-engineered command:

1. Update `protocol/fnirsi_dps150.ksy` (single source of truth)
2. Add binary wire example in a docstring or comment
3. Run `bash scripts/gen_kaitai.sh` to regenerate the Kaitai Python parser
4. Run `uv run python scripts/ksy_to_md.py ...` to regenerate the reference Markdown
5. Update TX encoder in `src/fnirsi_ps_control/protocol.py` if the command is host-initiated
6. Add byte-exact test in `tests/test_protocol.py`
7. Commit all: `.ksy` + generated files + Python + tests in one commit
