from __future__ import annotations

import unittest

from dictate.platform.generic import PynputHotkey


class Listener:
    def __init__(self, **kwargs: object) -> None:
        self.callbacks = kwargs
        self.started = False
        self.stopped = False
    def start(self) -> None: self.started = True
    def stop(self) -> None: self.stopped = True


class Key:
    name = "right_alt"


class HotkeyTests(unittest.TestCase):
    def test_matching_key_emits_one_press_and_release(self) -> None:
        events: list[str] = []
        listeners: list[Listener] = []
        def factory(**kwargs: object) -> Listener:
            listener = Listener(**kwargs)
            listeners.append(listener)
            return listener
        monitor = PynputHotkey("right_alt", lambda: events.append("press"), lambda: events.append("release"), factory)
        monitor.start()
        listener = listeners[0]
        listener.callbacks["on_press"](Key())
        listener.callbacks["on_press"](Key())
        listener.callbacks["on_release"](Key())
        self.assertEqual(["press", "release"], events)
        monitor.stop()
        self.assertTrue(listener.stopped)


if __name__ == "__main__":
    unittest.main()

