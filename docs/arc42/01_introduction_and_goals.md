# 1. Introduction and Goals

Documentation of the protocol for controlling the FNIRSI DPS-150 power supply by reverse engineering and implementation in the form of a Python library and CLI.

## Requirements Overview

| ID  | Description                                                          |
| --- | -------------------------------------------------------------------- |
| R-1 | Human-readable protocol description is generated                     |
| R-2 | Python implementation is generated                                   |
| R-3 | Provide reference implementation in the form of a Python library     |
| R-4 | Provide CLI based on library for interactive and scripted use        |
| R-5 | Can control voltage, current, output state                           |
| R-6 | Can read back basic state                                            |
| R-7 | Currently, no advanced functions (e.g., presets) need to be supported |


## Quality Goals

| Priority | Quality Goal    | Scenario                                                                  |
| -------- | --------------- | ------------------------------------------------------------------------- |
| 1        | Correctness     | Protocol implementation matches byte-exact captured device communication  |
| 2        | Maintainability | Single source of truth protocol definition (KSY) generates code and docs |
| 3        | Safety          | Errors (e.g., connection timeout) are detected and handled                |
| 4        | Usability       | CLI provides intuitive commands for interactive and scripted use          |
| 5        | Compatibility   | Only using common and stable Python libraries and tooling                 |
| 6        | Compatibility   | Runs on Linux systems without proprietary dependencies                    |
| 7        | Testability     | All protocol encoding/decoding is covered by automated unit tests         |

## Stakeholders

| Role                     | Description                                          | Goal, Intention                                                                            |
| ------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Technical enthusiast     | Uses device in everyday life                         | Wants to understand how the communication protocol works                                   |
| Linux user               | Uses Linux as primary OS                             | Wants to control the device from PC; manufacturer only provides a Windows tool             |
| Test automation engineer | Integrates power supply into automated test setups   | Wants scriptable, reproducible control of voltage and current for test sequences            |
| GUI developer            | Builds custom user interfaces for hardware           | Wants a clean library API without needing to understand protocol-level details              |
| Protocol researcher      | Reverse-engineers embedded device protocols          | Wants a well-documented, machine-readable protocol spec as a reference or starting point   |

