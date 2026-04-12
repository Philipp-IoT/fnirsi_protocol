"""Completeness check: every host-initiated command has a sequence entry.

Reads protocol/fnirsi_dps150.ksy and protocol/sequences.yaml directly
(no Kaitai dependency) and asserts that each command_id enum entry with
-x-direction == host_to_device or bidirectional appears as the `cmd` value
in at least one step across all sequences.

This catches the common mistake of adding a new command to the enum without
also defining its sequence in protocol/sequences.yaml.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROTOCOL_DIR = Path(__file__).parent.parent / "protocol"
KSY_PATH = PROTOCOL_DIR / "fnirsi_dps150.ksy"
SEQ_PATH = PROTOCOL_DIR / "sequences.yaml"


def _load_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def _host_initiated_commands(ksy: dict) -> set[str]:
    """Return names of commands that originate from the host."""
    cmd_enum: dict = ksy.get("enums", {}).get("command_id", {})
    result = set()
    for entry in cmd_enum.values():
        if not isinstance(entry, dict):
            continue
        direction = entry.get("-x-direction", "")
        if direction in ("host_to_device", "bidirectional"):
            result.add(str(entry.get("id", "")))
    return result


def _sequence_cmd_names(seq_data: dict) -> set[str]:
    """Return all cmd names referenced by any sequence step.

    A step's cmd field may be a combined label such as
    ``"get_device_name / get_hw_version / get_fw_version"`` — each part is
    added individually so the completeness check can match them.
    """
    sequences: list[dict] = seq_data.get("sequences", [])
    found: set[str] = set()
    for seq in sequences:
        for step in seq.get("steps", []):
            cmd = step.get("cmd")
            if cmd:
                for part in str(cmd).split(" / "):
                    found.add(part.strip())
    return found


def test_all_host_commands_have_sequence() -> None:
    ksy = _load_yaml(KSY_PATH)
    seq_data = _load_yaml(SEQ_PATH)
    host_cmds = _host_initiated_commands(ksy)
    seq_cmds = _sequence_cmd_names(seq_data)

    missing = host_cmds - seq_cmds
    assert not missing, (
        "The following host-initiated commands have no sequence entry in protocol/sequences.yaml:\n"
        + "\n".join(f"  - {c}" for c in sorted(missing))
        + "\n\nAdd a sequence step for each command in protocol/sequences.yaml."
    )


def test_sequences_file_is_present() -> None:
    assert SEQ_PATH.exists(), f"protocol/sequences.yaml not found at {SEQ_PATH}"
    seq_data = _load_yaml(SEQ_PATH)
    sequences = seq_data.get("sequences", [])
    assert sequences, f"No sequences found in {SEQ_PATH}"


@pytest.mark.parametrize("phase", ["connect", "active", "disconnect"])
def test_phase_has_at_least_one_sequence(phase: str) -> None:
    seq_data = _load_yaml(SEQ_PATH)
    sequences: list[dict] = seq_data.get("sequences", [])
    in_phase = [s for s in sequences if s.get("phase") == phase]
    assert in_phase, f"No sequence with phase='{phase}' found in protocol/sequences.yaml"
