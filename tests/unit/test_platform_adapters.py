from __future__ import annotations

import unittest

from dictate.platform.linux import LinuxAdapter
from dictate.platform.macos import MacOSAdapter
from dictate.platform.windows import WindowsAdapter


class Hotkey:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None: self.started = True
    def stop(self) -> None: self.stopped = True


class PlatformAdapterTests(unittest.TestCase):
    def test_all_platform_adapters_are_instantiable_and_fail_closed_for_target_safety(self) -> None:
        for adapter_type in (MacOSAdapter, WindowsAdapter, LinuxAdapter):
            with self.subTest(adapter=adapter_type.__name__):
                hotkeys: list[Hotkey] = []

                def factory(*args: object) -> Hotkey:
                    hotkey = Hotkey()
                    hotkeys.append(hotkey)
                    return hotkey

                adapter = adapter_type(factory)
                self.assertTrue(adapter.microphone_permission().available)
                self.assertTrue(adapter.trigger_permission().available)
                self.assertFalse(adapter.placement_permission().available)
                self.assertFalse(adapter.context_permission().available)
                self.assertIsNone(adapter.snapshot_target())
                self.assertFalse(adapter.target_matches(object()))
                self.assertFalse(adapter.insert_text(object(), "must-not-be-inserted"))

                adapter.start_hotkey("right_alt", lambda: None, lambda: None)
                adapter.stop_hotkey()
                self.assertTrue(hotkeys[0].started)
                self.assertTrue(hotkeys[0].stopped)


if __name__ == "__main__":
    unittest.main()

