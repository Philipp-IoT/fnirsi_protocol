# 6. Runtime View

<!-- ARC42 §6: Illustrate the behaviour of important use cases / scenarios
     as interaction or sequence diagrams. -->

## Scenario 1: Connect and Query Device Info

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Device
    participant DPS as FNIRSI DPS-150

    User->>CLI: fnirsi info --port /dev/ttyACM0
    CLI->>Device: open()
    Device->>DPS: CONNECT frame
    DPS-->>Device: CONNECT ACK
    Device->>DPS: QUERY_STATUS frame
    DPS-->>Device: STATUS blob
    Device-->>CLI: parsed DeviceStatus
    CLI-->>User: rich table output
```

_Placeholder — verify exact frame sequence and add error paths._

## Scenario 2: Set Voltage / Current

_To be filled. Add a sequence diagram similar to Scenario 1._

## Scenario 3: Output Enable / Disable

_To be filled._
