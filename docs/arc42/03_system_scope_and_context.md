# 3. System Scope and Context

<!-- ARC42 §3: Define what is INSIDE the system boundary and what is OUTSIDE.
     Show external actors/systems and the interfaces between them and the system. -->

## Business Context

<!-- Describe actors and data flows in plain English.
     Who/what interacts with the system and what information is exchanged? -->

_To be filled._

## Technical Context

<!-- Show the technical interfaces (protocols, data formats, channels).
     A context diagram is strongly recommended here. -->

```mermaid
graph LR
    User["Operator / Developer"]
    Lib["fnirsi-ps-control"]
    HW["FNIRSI DPS-150"]
    User -->|"CLI / Python API"| Lib
    Lib -->|"USB Serial CDC ACM 9600 8N1"| HW
```

_Diagram is a placeholder — refine with actual interface details._
