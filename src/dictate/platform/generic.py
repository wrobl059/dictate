"""Generic pynput press/release monitoring and keyboard insertion primitives."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class _Listener(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...


class PynputHotkey:
    """Emit one press and one release per configured held key."""

    def __init__(self, trigger: str, on_press: Callable[[], None], on_release: Callable[[], None], listener_factory: Callable[..., _Listener] | None = None) -> None:
        self._trigger = trigger
        self._on_press = on_press
        self._on_release = on_release
        self._listener_factory = listener_factory or self._listener
        self._listener_instance: _Listener | None = None
        self._held = False

    @staticmethod
    def _listener(**kwargs: object) -> _Listener:
        from pynput import keyboard

        return keyboard.Listener(**kwargs)

    def start(self) -> None:
        if self._listener_instance is not None:
            return
        self._listener_instance = self._listener_factory(on_press=self._press, on_release=self._release)
        self._listener_instance.start()

    def stop(self) -> None:
        if self._listener_instance is not None:
            self._listener_instance.stop()
            self._listener_instance = None
        self._held = False

    def _matches(self, key: object) -> bool:
        trigger = {"right_alt": "alt_r", "left_alt": "alt_l"}.get(self._trigger, self._trigger)
        name = getattr(key, "name", None)
        return name == trigger or str(key).removeprefix("Key.") == trigger

    def _press(self, key: object) -> None:
        if self._matches(key) and not self._held:
            self._held = True
            self._on_press()

    def _release(self, key: object) -> None:
        if self._matches(key) and self._held:
            self._held = False
            self._on_release()


def write_text(text: str, controller_factory: Callable[[], object] | None = None) -> None:
    """Inject text only when a platform adapter has just verified its target."""
    if not text:
        return
    if controller_factory is None:
        from pynput import keyboard

        controller_factory = keyboard.Controller
    controller = controller_factory()
    controller.write(text)

