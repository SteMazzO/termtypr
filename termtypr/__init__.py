"""TermTypr - A Python CLI application for practicing and improving typing speed."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("termtypr")
except PackageNotFoundError:
    # Running from a source tree without the package installed
    __version__ = "unknown"
