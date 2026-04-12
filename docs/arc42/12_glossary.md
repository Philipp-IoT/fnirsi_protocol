# 12. Glossary

<!-- ARC42 §12: Define domain-specific and technical terms used throughout the docs. -->

| Term | Definition |
|------|------------|
| CDC ACM | USB Communications Device Class Abstract Control Model — the USB profile used by the DPS-150 to present as a virtual serial port |
| DPS-150 | FNIRSI DPS-150, a 150 W regulated DC power supply with USB control interface |
| Kaitai Struct | A declarative binary format description language; the `.ksy` file is the single source of truth for the wire protocol |
| Frame | One complete protocol message: `[DIR][START][CMD][LEN][DATA×LEN][CHKSUM]` |
| DIR | Direction byte: `0xf1` host→device, `0xf0` device→host |
| CHKSUM | `(CMD + LEN + Σ DATA) mod 256` |
| ADR | Architecture Decision Record |
| ARC42 | A pragmatic template for architecture documentation (arc42.org) |
| Conventional Commits | A commit message specification enabling automated changelog and versioning |
| Semantic Release | Automated version management driven by commit message conventions |
| uv | Astral's fast Python package and project manager, used as the dev toolchain |

_Add terms as the documentation matures._
