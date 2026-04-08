#!/usr/bin/env bash
# Generate all artifacts from the Kaitai Struct spec.
#
# Outputs (committed as baseline):
#   protocol/generated/fnirsi_dps150.py   — Python parser (via ksc)
#   protocol/generated/fnirsi_dps150.dot  — raw Kaitai graphviz (reference)
#   docs/protocol/fnirsi_dps150.svg       — human-readable diagram (custom)
#
# Requires:
#   kaitai-struct-compiler on PATH
#     Debian/Ubuntu: sudo apt install kaitai-struct-compiler
#     Arch/Manjaro:  see AUR (kaitai-struct-compiler)
#     macOS:         brew install kaitai-struct-compiler
#     CI:            installed at /usr/bin/kaitai-struct-compiler on ubuntu-latest
#   graphviz (dot) on PATH
#   uv (Python runner)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KSY="${ROOT}/protocol/fnirsi_dps150.ksy"
OUTDIR="${ROOT}/protocol/generated"

# 1. Python parser
kaitai-struct-compiler --target python --outdir "${OUTDIR}" "${KSY}"
echo "Generated: ${OUTDIR}/fnirsi_dps150.py"

# 2. Raw Kaitai graphviz dot (kept for reference; not used for docs)
kaitai-struct-compiler --target graphviz --outdir "${OUTDIR}" "${KSY}"
echo "Generated: ${OUTDIR}/fnirsi_dps150.dot"

# 3. Human-readable diagram → docs
uv run python "${ROOT}/scripts/gen_protocol_diagram.py" \
    --ksy "${KSY}" \
    --svg "${ROOT}/docs/protocol/fnirsi_dps150.svg"
