# Protocol Reverse Engineering – Overview

> **Status:** Core protocol CONFIRMED against live hardware (2026-03-29).
> Values marked _TBD_ are still working hypotheses.

Device details (USB IDs, serial config, baud rate), the wire format, all
command IDs, payload types and enumerations are defined in the
[Kaitai Struct spec](reference.md), embedded in the
[Specification](spec.md) page.

---

## Documents

| Document | Contents |
|----------|----------|
| [spec.md](spec.md) | Protocol specification (embeds the `.ksy` — single source of truth) |
| [session.md](session.md) | Session lifecycle: connect → operate → disconnect |
| [reference.md](reference.md) | Auto-generated reference from the Kaitai Struct spec |
| [captures.md](captures.md) | Raw capture log files (binary excluded via .gitignore) |

---

## RE Methodology

See [methodology.md](../re_methodology.md) for the step-by-step capture workflow.
