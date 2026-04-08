#!/usr/bin/env bash
# Generate Python parser from the Kaitai Struct spec using ksc.
# Output lands in protocol/generated/ and is committed as a baseline.
#
# Requires: kaitai-struct-compiler on PATH
#   Debian/Ubuntu: sudo apt install kaitai-struct-compiler
#   Arch/Manjaro:  see AUR (kaitai-struct-compiler)
#   macOS:         brew install kaitai-struct-compiler
#   CI:            installed at /usr/bin/kaitai-struct-compiler on ubuntu-latest
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KSY="${ROOT}/protocol/fnirsi_dps150.ksy"
OUTDIR="${ROOT}/protocol/generated"

kaitai-struct-compiler --target python --outdir "${OUTDIR}" "${KSY}"
echo "Generated: ${OUTDIR}/fnirsi_dps150.py"

kaitai-struct-compiler --target graphviz --outdir "${OUTDIR}" "${KSY}"
echo "Generated: ${OUTDIR}/fnirsi_dps150.dot"

dot -Tsvg "${OUTDIR}/fnirsi_dps150.dot" -o "${OUTDIR}/fnirsi_dps150.svg"
echo "Generated: ${OUTDIR}/fnirsi_dps150.svg"

cp "${OUTDIR}/fnirsi_dps150.svg" "${ROOT}/docs/protocol/fnirsi_dps150.svg"
echo "Copied SVG: docs/protocol/fnirsi_dps150.svg"
