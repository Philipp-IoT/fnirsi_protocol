# 7. Deployment View

<!-- ARC42 §7: Describe the hardware and software environment the system runs in.
     Show how building blocks map onto infrastructure. -->

## Infrastructure Level 1

```mermaid
graph LR
    subgraph "Host PC (Linux / Windows / macOS)"
        PY["Python ≥ 3.11"]
        PKG["fnirsi-ps-control package"]
        SERIAL["pyserial"]
        PY --> PKG
        PKG --> SERIAL
    end
    subgraph "USB"
        CDC["CDC ACM device node<br/>/dev/ttyACM* or COMx"]
    end
    subgraph "Hardware"
        DPS["FNIRSI DPS-150"]
    end
    SERIAL -->|"USB Serial"| CDC
    CDC --> DPS
```

_Placeholder — add OS-specific notes and any CI/packaging deployment details._

## Deployment Notes

<!-- How is the package distributed? (PyPI, git clone, uv tool install, …)
     Are there any OS-level driver requirements? -->

_To be filled._
