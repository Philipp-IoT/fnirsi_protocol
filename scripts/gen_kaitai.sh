#!/usr/bin/env bash
# Generate Python parser from the Kaitai Struct spec.
# Output lands in protocol/generated/ and is committed as a baseline.
#
# Requires: kaitai-struct-compiler 0.10 on PATH
#   Linux:  snap install kaitai-struct-compiler
#   macOS:  brew install kaitai-struct-compiler
#   Manual: download ZIP from https://github.com/kaitai-io/kaitai_struct_compiler/releases
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KSY="${ROOT}/protocol/fnirsi_dps150.ksy"
OUTDIR="${ROOT}/protocol/generated"

kaitai-struct-compiler --target python --outdir "${OUTDIR}" "${KSY}"
echo "Generated: ${OUTDIR}/fnirsi_dps150.py"
