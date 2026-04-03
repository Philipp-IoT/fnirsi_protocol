"""Command-line interface for fnirsi_ps_control."""

from __future__ import annotations

import logging
import time
from importlib.metadata import version
from typing import Annotated

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from fnirsi_ps_control.device import DPS150

app = typer.Typer(
    name="fnirsi",
    help="Control and monitor the FNIRSI DPS-150 regulated power supply.",
    no_args_is_help=True,
)
console = Console()

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------
PortOpt = Annotated[
    str,
    typer.Option("--port", "-p", help="Serial port (e.g. /dev/ttyACM0 or COM3)."),
]
BaudOpt = Annotated[
    int,
    typer.Option("--baudrate", "-b", help="Baud rate."),
]

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def ver() -> None:
    """Print the installed package version."""
    console.print(f"fnirsi-ps-control {version('fnirsi-ps-control')}")


@app.command()
def info(port: PortOpt, baudrate: BaudOpt = 9600) -> None:
    """Query and display the current device status."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        status = ps.get_status()

    table = Table(title="FNIRSI DPS-150 Status", show_header=True)
    table.add_column("Parameter", style="bold")
    table.add_column("Value")
    table.add_row("Voltage (set)", f"{status.voltage_set_v:.3f} V")
    table.add_row("Voltage (measured)", f"{status.voltage_out_v:.3f} V")
    table.add_row("Current (limit)", f"{status.current_set_a:.3f} A")
    table.add_row("Current (measured)", f"{status.current_out_a:.3f} A")
    table.add_row("Power (measured)", f"{status.power_out_w:.3f} W")
    table.add_row(
        "Output",
        "[green]ON[/green]" if status.output_enabled else "[red]OFF[/red]",
    )
    console.print(table)


@app.command("set-voltage")
def set_voltage(
    voltage: Annotated[float, typer.Argument(help="Target voltage in volts.")],
    port: PortOpt,
    baudrate: BaudOpt = 9600,
) -> None:
    """Set the output voltage."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        ps.set_voltage(voltage)
    console.print(f"[green]✓[/green] Voltage set to {voltage:.3f} V")


@app.command("set-current")
def set_current(
    current: Annotated[float, typer.Argument(help="Current limit in amps.")],
    port: PortOpt,
    baudrate: BaudOpt = 9600,
) -> None:
    """Set the output current limit."""
    with DPS150(port=port, baudrate=baudrate) as ps:
        ps.set_current_limit(current)
    console.print(f"[green]✓[/green] Current limit set to {current:.3f} A")


@app.command()
def output(
    state: Annotated[str, typer.Argument(help="'on' or 'off'.")],
    port: PortOpt,
    baudrate: BaudOpt = 9600,
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


@app.command()
def monitor(
    port: PortOpt,
    baudrate: BaudOpt = 9600,
    interval: Annotated[float, typer.Option(help="Refresh interval in seconds.")] = 0.6,
) -> None:
    """Live monitor of output voltage, current and power (PUSH_OUTPUT stream).

    Press Ctrl-C to stop.
    """

    def _make_table(vout: float, iout: float, pout: float, ts: float) -> Table:
        t = Table(title="FNIRSI DPS-150 — Live Output", show_header=True)
        t.add_column("Measurement", style="bold")
        t.add_column("Value", justify="right")
        t.add_row("Voltage", f"[cyan]{vout:.3f}[/cyan] V")
        t.add_row("Current", f"[cyan]{iout:.4f}[/cyan] A")
        t.add_row("Power", f"[cyan]{pout:.3f}[/cyan] W")
        t.add_row("Time", f"{ts:.1f} s")
        return t

    start = time.monotonic()
    with DPS150(port=port, baudrate=baudrate) as ps:
        with Live(console=console, refresh_per_second=4) as live:
            try:
                while True:
                    push = ps.read_push_output()
                    elapsed = time.monotonic() - start
                    live.update(_make_table(push.vout_v, push.iout_a, push.pout_w, elapsed))
                    time.sleep(interval)
            except KeyboardInterrupt:
                pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    app()


if __name__ == "__main__":
    main()
