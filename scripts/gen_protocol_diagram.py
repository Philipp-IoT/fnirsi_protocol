#!/usr/bin/env python3
"""Generate a human-readable protocol diagram from protocol/fnirsi_dps150.ksy.

Produces a graphviz dot source and renders it to SVG.  Replaces the
Kaitai-generated graphviz output which cannot render compound switch-on
expressions in a readable way.

Usage:
    uv run python scripts/gen_protocol_diagram.py \\
        --ksy protocol/fnirsi_dps150.ksy \\
        --svg docs/protocol/fnirsi_dps150.svg
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Protocol constants (must match the direction enum in the .ksy)
# ---------------------------------------------------------------------------
_DIR_TX = 0xF1  # host → device
_DIR_RX = 0xF0  # device → host

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_C_TX_HDR = "#1565C0"   # TX table header (dark blue)
_C_TX_ROW = "#E3F2FD"   # TX row even
_C_TX_ALT = "#BBDEFB"   # TX row odd
_C_RX_HDR = "#1B5E20"   # RX table header (dark green)
_C_RX_ROW = "#E8F5E9"   # RX row even
_C_RX_ALT = "#C8E6C9"   # RX row odd
_C_FR_HDR = "#37474F"   # Frame header (dark grey)
_C_FR_ROW = "#ECEFF1"   # Frame body
_C_MG_HDR = "#E65100"   # Magic frame header (deep orange)
_C_MG_ROW = "#FFF3E0"   # Magic frame body
_C_FG     = "white"

# ---------------------------------------------------------------------------
# Friendly payload labels (strip the verbose _payload suffix)
# ---------------------------------------------------------------------------
_PAYLOAD_LABELS: dict[str, str] = {
    "query_payload":          "query (0x00)",
    "connect_payload":        "connect_state",
    "ready_payload":          "u8 ready",
    "string_payload":         "ASCII string",
    "float32_payload":        "f32 LE",
    "output_enable_payload":  "output_state",
    "push_output_payload":    "vout · iout · pout",
    "full_status_payload":    "full status blob",
}


def _fmt_payload(name: str) -> str:
    return _PAYLOAD_LABELS.get(name, name)


def _h(s: str) -> str:
    """Minimal HTML escaping for graphviz HTML-like labels."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# .ksy helpers
# ---------------------------------------------------------------------------

def load_ksy(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def payload_maps(ksy: dict[str, Any]) -> tuple[dict[int, str], dict[int, str]]:
    """Return (tx_map, rx_map): cmd_byte → payload_type_name."""
    cmd_body_seq: list[dict[str, Any]] = (
        ksy.get("types", {}).get("command_body", {}).get("seq", [])
    )
    raw_cases: dict[int, str] = {}
    for field in cmd_body_seq:
        if field.get("id") == "payload":
            t = field.get("type", {})
            if isinstance(t, dict):
                raw_cases = t.get("cases", {})
            break

    tx: dict[int, str] = {}
    rx: dict[int, str] = {}
    for compound_key, payload_type in raw_cases.items():
        dir_byte = (compound_key >> 8) & 0xFF
        cmd_byte = compound_key & 0xFF
        (tx if dir_byte == _DIR_TX else rx)[cmd_byte] = payload_type
    return tx, rx


# ---------------------------------------------------------------------------
# Graphviz HTML-like label builders
# ---------------------------------------------------------------------------

def _cmd_rows(payload_map: dict[int, str], cmd_names: dict[int, str],
              row_bg: str, alt_bg: str) -> str:
    html = ""
    for i, (cmd_val, payload_type) in enumerate(sorted(payload_map.items())):
        name = cmd_names.get(cmd_val, f"?0x{cmd_val:02X}?")
        bg = row_bg if i % 2 == 0 else alt_bg
        html += (
            f'<TR BGCOLOR="{bg}">'
            f'<TD ALIGN="LEFT"><FONT FACE="Courier New,Courier,monospace">'
            f'<B>0x{cmd_val:02X}</B></FONT></TD>'
            f'<TD ALIGN="LEFT">{_h(name)}</TD>'
            f'<TD ALIGN="LEFT"><I>{_h(_fmt_payload(payload_type))}</I></TD>'
            f'</TR>\n'
        )
    return html


def frame_label() -> str:
    return (
        '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        f'<TR><TD COLSPAN="6" BGCOLOR="{_C_FR_HDR}">'
        f'<FONT COLOR="{_C_FG}"><B>Wire Frame</B></FONT></TD></TR>'
        f'<TR BGCOLOR="{_C_FR_ROW}">'
        '<TD ALIGN="CENTER"><B>DIR</B><BR/>0xF0 / 0xF1<BR/>1 B</TD>'
        '<TD ALIGN="CENTER"><B>START</B><BR/>0xA1 / 0xB0<BR/>0xB1 / 0xC1<BR/>1 B</TD>'
        '<TD ALIGN="CENTER"><B>CMD</B><BR/>see tables<BR/>1 B</TD>'
        '<TD ALIGN="CENTER"><B>LEN</B><BR/>N<BR/>1 B</TD>'
        '<TD ALIGN="CENTER"><B>DATA</B><BR/>payload<BR/>N B</TD>'
        '<TD ALIGN="CENTER"><B>CHKSUM</B><BR/>(CMD+LEN<BR/>+ΣDATA)%256<BR/>1 B</TD>'
        '</TR>'
        '</TABLE>'
    )


def tx_label(tx_map: dict[int, str], cmd_names: dict[int, str]) -> str:
    rows = _cmd_rows(tx_map, cmd_names, _C_TX_ROW, _C_TX_ALT)
    return (
        '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        f'<TR><TD COLSPAN="3" BGCOLOR="{_C_TX_HDR}">'
        f'<FONT COLOR="{_C_FG}"><B>TX — host→device (DIR=0xF1)</B></FONT></TD></TR>'
        f'<TR BGCOLOR="{_C_TX_HDR}">'
        f'<TD><FONT COLOR="{_C_FG}"><B>CMD</B></FONT></TD>'
        f'<TD><FONT COLOR="{_C_FG}"><B>Name</B></FONT></TD>'
        f'<TD><FONT COLOR="{_C_FG}"><B>Payload</B></FONT></TD></TR>\n'
        + rows +
        '</TABLE>'
    )


def rx_label(rx_map: dict[int, str], cmd_names: dict[int, str]) -> str:
    rows = _cmd_rows(rx_map, cmd_names, _C_RX_ROW, _C_RX_ALT)
    return (
        '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        f'<TR><TD COLSPAN="3" BGCOLOR="{_C_RX_HDR}">'
        f'<FONT COLOR="{_C_FG}"><B>RX — device→host (DIR=0xF0)</B></FONT></TD></TR>'
        f'<TR BGCOLOR="{_C_RX_HDR}">'
        f'<TD><FONT COLOR="{_C_FG}"><B>CMD</B></FONT></TD>'
        f'<TD><FONT COLOR="{_C_FG}"><B>Name</B></FONT></TD>'
        f'<TD><FONT COLOR="{_C_FG}"><B>Payload</B></FONT></TD></TR>\n'
        + rows +
        '</TABLE>'
    )


def magic_label() -> str:
    return (
        '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        f'<TR><TD BGCOLOR="{_C_MG_HDR}">'
        f'<FONT COLOR="{_C_FG}"><B>Session Magic  (TX only, START=0xB0)</B></FONT></TD></TR>'
        f'<TR BGCOLOR="{_C_MG_ROW}"><TD ALIGN="LEFT">'
        'DIR=0xF1 · START=0xB0 · <FONT FACE="Courier New,Courier,monospace">00 01 01 01</FONT><BR/>'
        '<I>Non-standard — no CMD / LEN / CHKSUM</I>'
        '</TD></TR>'
        '</TABLE>'
    )


# ---------------------------------------------------------------------------
# Dot source assembly
# ---------------------------------------------------------------------------

def build_dot(ksy: dict[str, Any]) -> str:
    cmd_names: dict[int, str] = ksy.get("enums", {}).get("command_id", {})
    tx_map, rx_map = payload_maps(ksy)

    fl = frame_label()
    tl = tx_label(tx_map, cmd_names)
    rl = rx_label(rx_map, cmd_names)
    ml = magic_label()

    return f"""\
digraph fnirsi_dps150 {{
    graph [
        rankdir  = TB
        fontname = "Helvetica Neue,Helvetica,Arial,sans-serif"
        bgcolor  = "white"
        pad      = 0.5
        nodesep  = 0.8
        ranksep  = 0.7
    ]
    node [
        fontname = "Helvetica Neue,Helvetica,Arial,sans-serif"
        shape    = plaintext
        margin   = 0
    ]
    edge [
        fontname = "Helvetica Neue,Helvetica,Arial,sans-serif"
        fontsize = 10
    ]

    frame [label=<{fl}>]
    tx    [label=<{tl}>]
    rx    [label=<{rl}>]
    magic [label=<{ml}>]

    {{rank=same tx rx magic}}

    frame -> tx    [label="DIR=0xF1\\nSTART≠0xB0"
                    color="{_C_TX_HDR}" fontcolor="{_C_TX_HDR}"]
    frame -> magic [label="DIR=0xF1\\nSTART=0xB0"
                    color="{_C_MG_HDR}" fontcolor="{_C_MG_HDR}"]
    frame -> rx    [label="DIR=0xF0"
                    color="{_C_RX_HDR}" fontcolor="{_C_RX_HDR}"]
}}
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ksy", required=True, type=Path, help="Path to .ksy file")
    p.add_argument("--svg", required=True, type=Path, help="Output SVG path")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ksy = load_ksy(args.ksy)
    dot_src = build_dot(ksy)

    args.svg.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["dot", "-Tsvg"],
        input=dot_src,
        capture_output=True,
        text=True,
        check=True,
    )
    args.svg.write_text(result.stdout)
    print(f"Generated: {args.svg}")


if __name__ == "__main__":
    main()
