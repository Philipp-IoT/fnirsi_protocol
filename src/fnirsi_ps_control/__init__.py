"""fnirsi_ps_control – PC control for the FNIRSI DPS-150 power supply."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__: str = version("fnirsi-ps-control")
except PackageNotFoundError:  # running from source / editable install not yet built
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
