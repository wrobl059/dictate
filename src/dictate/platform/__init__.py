"""Platform-specific adapters isolated behind a narrow contract."""

import sys

from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot


def current_platform() -> PlatformAdapter:
	"""Return the supported adapter for this host, or fail before recording."""
	if sys.platform == "darwin":
		from dictate.platform.macos import MacOSAdapter

		return MacOSAdapter()
	if sys.platform == "win32":
		from dictate.platform.windows import WindowsAdapter

		return WindowsAdapter()
	if sys.platform.startswith("linux"):
		from dictate.platform.linux import LinuxAdapter

		return LinuxAdapter()
	raise RuntimeError(f"unsupported operating system: {sys.platform}")


__all__ = ("Capability", "PlatformAdapter", "TargetSnapshot", "current_platform")

