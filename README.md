# fnirsi-ps-control

Protocol reverse engineering and Python CLI demo for the **FNIRSI DPS-150** regulated
power supply.

The `.ksy` Kaitai Struct spec in `protocol/` is the single source of truth for the wire
protocol. A generated Python parser handles all RX decoding; TX encoding is handwritten.

> **Documentation:** [GitHub Pages](https://pbolte.github.io/fnirsi_ps_control) (deployed from `main`)

---

## Hardware

| Property | Value |
|---|---|
| USB VID / PID | `0x2e3c` / `0x5740` (Artery AT32 Virtual COM Port) |
| Serial config | 9600 baud, 8N1 |
| DTR / RTS | DTR=**off**, RTS=**on** |
| Device file | `/dev/ttyACM0` (Linux) or `COMx` (Windows) |

## Wire format

```
[DIR:1][START:1][CMD:1][LEN:1][DATA×LEN][CHKSUM:1]

DIR    0xf1 host→device | 0xf0 device→host
CHKSUM (CMD + LEN + Σ DATA) mod 256
```

Floats are IEEE 754 32-bit little-endian. See `protocol/fnirsi_dps150.ksy` for the full
specification.

---

## Quick start

```sh
uv sync --extra dev
uv run fnirsi --help
```

### CLI commands

```
fnirsi ver                              # installed package version
fnirsi info         --port /dev/ttyACM0
fnirsi set-voltage  12.0 --port /dev/ttyACM0
fnirsi set-current  1.5  --port /dev/ttyACM0
fnirsi output       on   --port /dev/ttyACM0
fnirsi monitor           --port /dev/ttyACM0   # live Vout/Iout/Pout stream
```

---

## Protocol development

Regenerate the Kaitai Python parser after editing `protocol/fnirsi_dps150.ksy`:

```sh
bash scripts/gen_kaitai.sh
```

Regenerate the protocol reference Markdown:

```sh
uv run python scripts/ksy_to_md.py \
    --ksy protocol/fnirsi_dps150.ksy \
    --out docs/protocol/reference.md
```

Run tests:

```sh
uv run pytest
```

Pre-captured USB traffic logs live in `protocol/captures/`. The legacy implementation
(pre-restructure) is preserved in `legacy/` as reference.

---

## Documentation

Install the docs dependencies and serve locally:

```sh
uv sync --extra docs
uv run mkdocs serve
```

Build a static site into `site/`:

```sh
uv run mkdocs build
```

---

## Repository layout

```
protocol/
  fnirsi_dps150.ksy       single source of truth for the wire protocol
  generated/
    fnirsi_dps150.py      ksc-generated Python parser (committed baseline)
  captures/               raw USB capture logs (.txt)
scripts/
  gen_kaitai.sh           wraps kaitai-struct-compiler invocation
  ksy_to_md.py            .ksy → docs/protocol/reference.md
src/fnirsi_ps_control/    Python library + CLI
tests/                    byte-exact TX tests + Kaitai RX parse tests
docs/                     MkDocs source (deployed to GH Pages)
legacy/                   pre-restructure code (reference only)
```

## License

MIT
