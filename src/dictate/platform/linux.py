"""Conservative Linux integration without display-server-specific target inspection."""

from collections.abc import Callable

from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.platform.generic import PynputHotkey


class LinuxAdapter(PlatformAdapter):
    """Use pynput for the trigger and fail safely until target identity is available."""

    def __init__(self, hotkey_factory: Callable[..., PynputHotkey] = PynputHotkey) -> None:
        self._hotkey_factory = hotkey_factory
        self._hotkey: PynputHotkey | None = None

    def microphone_permission(self) -> Capability:
        return Capability(True)

    def trigger_permission(self) -> Capability:
        return Capability(True)

    def placement_permission(self) -> Capability:
        return Capability(False, "use a supported desktop session with original text-target verification")

    def context_permission(self) -> Capability:
        return Capability(False, "enable desktop accessibility support to use optional destination context")

    def snapshot_target(self) -> TargetSnapshot | None:
        return None

    def read_context(self, target: TargetSnapshot, limit: int) -> str | None:
        return None

    def target_matches(self, target: TargetSnapshot) -> bool:
        return False

    def insert_text(self, target: TargetSnapshot, text: str) -> bool:
        return False

    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None:
        self._hotkey = self._hotkey_factory(trigger, on_press, on_release)
        self._hotkey.start()

    def stop_hotkey(self) -> None:
        if self._hotkey is not None:
            self._hotkey.stop()
            self._hotkey = None

    def recovery_instruction(self) -> str:
        return "run dictate serve --recover in this service process"

    pass

