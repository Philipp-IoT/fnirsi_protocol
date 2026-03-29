"""Command-line interface for fnirsi_ps_control."""

from __future__ import annotations

import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from fnirsi_ps_control.device import DPS150
from fnirsi_ps_control import __version__

app = typer.Typer(
    name="fnirsi",
    help="PC control for the FNIRSI DPS-150 regulated power supply.",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------
PortArg = Annotated[
    str,
    typer.Option("--port", "-p", help="Serial port (e.g. /dev/ttyACM0 or COM3)."),
]
BaudArg = Annotated[
    int,
    typer.Option("--baudrate", "-b", help="Baud rate."),
]

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Print the installed package version."""
    console.print(f"fnirsi-ps-control {__version__}")


@app.command()
def info(
    port: PortArg,
    baudrate: BaudArg = 115200,
) -> None:
    """Query and display the current device status."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        status = ps.get_status()

    table = Table(title="FNIRSI DPS-150 Status", show_header=True)
    table.add_column("Parameter", style="bold")
    table.add_column("Value")

    table.add_row("Voltage (set)", f"{status.voltage_set_mv / 1000:.3f} V")
    table.add_row("Voltage (measured)", f"{status.voltage_meas_mv / 1000:.3f} V")
    table.add_row("Current (limit)", f"{status.current_set_ma / 1000:.3f} A")
    table.add_row("Current (measured)", f"{status.current_meas_ma / 1000:.3f} A")
    table.add_row("Power (measured)", f"{status.power_mw / 1000:.3f} W")
    table.add_row("Output", "[green]ON[/green]" if status.output_enabled else "[red]OFF[/red]")

    console.print(table)


@app.command("set-voltage")
def set_voltage(
    voltage: Annotated[float, typer.Argument(help="Target voltage in volts.")],
    port: PortArg,
    baudrate: BaudArg = 115200,
) -> None:
    """Set the output voltage."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        ps.set_voltage(voltage)
    console.print(f"[green]✓[/green] Voltage set to {voltage:.3f} V")


@app.command("set-current")
def set_current(
    current: Annotated[float, typer.Argument(help="Current limit in amps.")],
    port: PortArg,
    baudrate: BaudArg = 115200,
) -> None:
    """Set the output current limit."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        ps.set_current_limit(current)
    console.print(f"[green]✓[/green] Current limit set to {current:.3f} A")


@app.command("output")
def output(
    state: Annotated[str, typer.Argument(help="'on' or 'off'.")],
    port: PortArg,
    baudrate: BaudArg = 115200,
) -> None:
    """Enable or disable the power supply output."""
    s = state.lower().strip()
    if s not in {"on", "off"}:
        console.print("[red]Error:[/red] state must be 'on' or 'off'")
        raise typer.Exit(code=1)

    with DPS150(port=port, baudrate=baudrate) as ps:
        if s == "on":
            ps.enable_output()
        else:
            ps.disable_output()

    tag = "[green]ON[/green]" if s == "on" else "[red]OFF[/red]"
    console.print(f"Output turned {tag}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    app()


if __name__ == "__main__":
    main()
