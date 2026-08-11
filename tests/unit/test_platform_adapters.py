from __future__ import annotations

import unittest
from types import ModuleType
from unittest.mock import patch

from dictate.platform.base import TargetSnapshot
from dictate.platform.linux import LinuxAdapter
from dictate.platform.macos import MacOSAdapter, _PyObjCAccessibility, write_unicode_keyboard_text
from dictate.platform.windows import WindowsAdapter


class Hotkey:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None: self.started = True
    def stop(self) -> None: self.stopped = True


class Accessibility:
    def __init__(self) -> None:
        self.allowed = True
        self.application, self.window, self.element = object(), object(), object()
        self.app_title: str | None = None
        self.editable_target = True
        self.replacements: list[tuple[object, str]] = []
        self.replacement_succeeds = True

    def trusted(self) -> bool: return self.allowed
    def focused_target(self) -> tuple[object, object, object] | None: return (self.application, self.window, self.element)
    def application_id(self, application: object) -> str | None: return "app" if application is self.application else None
    def application_title(self, application: object) -> str | None: return self.app_title if application is self.application else None
    def window_id(self, window: object) -> str | None: return "window" if window is self.window else None
    def editable(self, element: object) -> bool: return self.editable_target and element is self.element
    def same(self, first: object, second: object) -> bool: return first is second
    def replace_selected_text(self, element: object, text: str) -> bool:
        self.replacements.append((element, text))
        return self.replacement_succeeds


class PlatformAdapterTests(unittest.TestCase):
    def test_platform_runtime_acquisition_uses_one_documented_route(self) -> None:
        for adapter_type in (MacOSAdapter, WindowsAdapter, LinuxAdapter):
            with self.subTest(adapter=adapter_type.__name__):
                commands: list[tuple[str, ...]] = []
                result = adapter_type(lambda *_args: Hotkey()).acquire_external_runtime(
                    "whisper-runtime", lambda command: commands.append(tuple(command)) or True
                )
                self.assertTrue(result.acquired)
                self.assertEqual(1, len(commands))
                self.assertFalse(adapter_type(lambda *_args: Hotkey()).acquire_external_runtime("unknown", lambda _command: True).acquired)

    def test_non_macos_adapters_fail_closed_for_target_safety(self) -> None:
        for adapter_type in (WindowsAdapter, LinuxAdapter):
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

    def test_macos_microphone_authorization_is_explicit_and_content_free(self) -> None:
        calls: list[object] = []
        adapter = MacOSAdapter(
            lambda *_args: Hotkey(),
            microphone_authorized=lambda: calls.append(object()) or True,
            accessibility_factory=Accessibility,
        )
        self.assertTrue(adapter.microphone_permission().available)
        self.assertEqual(1, len(calls))

        denied = MacOSAdapter(lambda *_args: Hotkey(), microphone_authorized=lambda: False, accessibility_factory=Accessibility)
        capability = denied.microphone_permission()
        self.assertFalse(capability.available)
        self.assertIn("Microphone", capability.remediation or "")

    def test_macos_accessibility_snapshot_revalidates_and_releases_target(self) -> None:
        accessibility = Accessibility()
        adapter = MacOSAdapter(lambda *_args: Hotkey(), microphone_authorized=lambda: True, accessibility_factory=lambda: accessibility)
        self.assertTrue(adapter.placement_permission().available)
        target = adapter.snapshot_target()
        self.assertIsInstance(target, TargetSnapshot)
        assert target is not None
        self.assertTrue(adapter.target_matches(target))
        self.assertTrue(adapter.insert_text(target, "verified text"))
        self.assertEqual([(accessibility.element, "verified text")], accessibility.replacements)
        adapter.release_target(target)
        self.assertFalse(adapter.target_matches(target))
        self.assertFalse(adapter.insert_text(target, "must-not-be-inserted"))

    def test_macos_focus_change_or_missing_accessibility_never_inserts(self) -> None:
        accessibility = Accessibility()
        adapter = MacOSAdapter(lambda *_args: Hotkey(), microphone_authorized=lambda: True, accessibility_factory=lambda: accessibility)
        target = adapter.snapshot_target()
        assert target is not None
        accessibility.element = object()
        self.assertFalse(adapter.target_matches(target))
        self.assertFalse(adapter.insert_text(target, "must-not-be-inserted"))
        self.assertEqual([], accessibility.replacements)

        unavailable = MacOSAdapter(lambda *_args: Hotkey(), microphone_authorized=lambda: True, accessibility_factory=lambda: (_ for _ in ()).throw(ImportError()))
        self.assertFalse(unavailable.placement_permission().available)
        self.assertIsNone(unavailable.snapshot_target())

    def test_macos_does_not_broaden_keyboard_input_for_ordinary_apps(self) -> None:
        accessibility = Accessibility()
        accessibility.replacement_succeeds = False
        written: list[str] = []
        adapter = MacOSAdapter(
            lambda *_args: Hotkey(),
            microphone_authorized=lambda: True,
            accessibility_factory=lambda: accessibility,
            text_writer=written.append,
        )
        target = adapter.snapshot_target()
        assert target is not None

        self.assertFalse(adapter.insert_text(target, "ordinary app text"))
        self.assertEqual([], written)

        accessibility.element = object()
        self.assertFalse(adapter.insert_text(target, "must-not-be-inserted"))
        self.assertEqual([], written)

    def test_macos_uses_keyboard_input_only_for_slack(self) -> None:
        accessibility = Accessibility()
        accessibility.app_title = "Slack"
        written: list[str] = []
        adapter = MacOSAdapter(
            lambda *_args: Hotkey(),
            microphone_authorized=lambda: True,
            accessibility_factory=lambda: accessibility,
            text_writer=written.append,
        )
        target = adapter.snapshot_target()
        assert target is not None

        self.assertTrue(adapter.insert_text(target, "slack text"))
        self.assertEqual(["slack text"], written)
        self.assertEqual([], accessibility.replacements)

        accessibility.element = object()
        self.assertFalse(adapter.insert_text(target, "must-not-be-inserted"))
        self.assertEqual(["slack text"], written)

    def test_macos_slack_keyboard_writer_failure_is_fail_closed(self) -> None:
        accessibility = Accessibility()
        accessibility.app_title = "Slack"
        adapter = MacOSAdapter(
            lambda *_args: Hotkey(),
            microphone_authorized=lambda: True,
            accessibility_factory=lambda: accessibility,
            text_writer=lambda _text: (_ for _ in ()).throw(RuntimeError()),
        )
        target = adapter.snapshot_target()
        assert target is not None

        self.assertFalse(adapter.insert_text(target, "must-not-be-inserted"))

    def test_quartz_unicode_writer_posts_a_utf16_key_pair_without_clipboard(self) -> None:
        events: list[tuple[int, bool, object]] = []
        setters: list[tuple[object, int, str]] = []
        posted: list[tuple[int, object]] = []

        def event_factory(_source: object, key_code: int, down: bool) -> object:
            event = object()
            events.append((key_code, down, event))
            return event

        write_unicode_keyboard_text(
            "A😀",
            event_factory=event_factory,
            unicode_setter=lambda event, length, text: setters.append((event, length, text)),
            event_poster=lambda tap, event: posted.append((tap, event)),
            event_tap=7,
        )

        self.assertEqual([(0, True), (0, False)], [(key_code, down) for key_code, down, _event in events])
        self.assertEqual([(events[0][2], 3, "A😀"), (events[1][2], 3, "A😀")], setters)
        self.assertEqual([(7, events[0][2]), (7, events[1][2])], posted)

    def test_quartz_unicode_writer_ignores_empty_text(self) -> None:
        calls: list[object] = []
        write_unicode_keyboard_text(
            "",
            event_factory=lambda *_args: calls.append(object()),
            unicode_setter=lambda *_args: calls.append(object()),
            event_poster=lambda *_args: calls.append(object()),
            event_tap=7,
        )
        self.assertEqual([], calls)

    def test_pyobjc_bridge_uses_stable_attribute_keys_when_constants_are_not_exported(self) -> None:
        module = ModuleType("ApplicationServices")
        module.AXIsProcessTrusted = lambda: True
        module.AXUIElementCreateSystemWide = lambda: object()
        pid_result: list[tuple[int, int]] = [(0, 42)]
        module.AXUIElementGetPid = lambda _element, _pid: pid_result[0]
        queried: list[str] = []
        editable_value: list[object | None] = [True]
        window_number: list[object | None] = [7]
        role: list[object] = [7]

        def copy(_element: object, attribute: str, out_value: object) -> tuple[int, object]:
            self.assertIsNone(out_value)
            queried.append(attribute)
            if attribute == "AXEditable":
                return (0, editable_value[0])
            if attribute == "AXWindowNumber":
                return (0, window_number[0])
            if attribute == "AXRole":
                return (0, role[0])
            return (0, 7)

        module.AXUIElementCopyAttributeValue = copy
        module.AXUIElementSetAttributeValue = lambda _element, _attribute, _value: 0
        module.kAXFocusedApplicationAttribute = "AXFocusedApplication"
        module.kAXFocusedUIElementAttribute = "AXFocusedUIElement"
        module.kAXFocusedWindowAttribute = "AXFocusedWindow"
        module.kAXRoleAttribute = "AXRole"
        module.kAXSelectedTextAttribute = "AXSelectedText"
        module.kAXTextAreaRole = 7
        module.kAXTextFieldRole = 8
        with patch.dict("sys.modules", {"ApplicationServices": module}):
            bridge = _PyObjCAccessibility()
            self.assertEqual("window:7", bridge.window_id(object()))
            window_number[0] = None
            self.assertEqual("window-pid:42", bridge.window_id(object()))
            pid_result[0] = (1, 42)
            self.assertIsNone(bridge.window_id(object()))
            pid_result[0] = (0, 42)
            self.assertTrue(bridge.editable(object()))
            role[0] = "AXComboBox"
            self.assertTrue(bridge.editable(object()))
            role[0] = "AXGroup"
            self.assertTrue(bridge.editable(object()))
            editable_value[0] = None
            self.assertFalse(bridge.editable(object()))
            role[0] = 7
            self.assertTrue(bridge.editable(object()))
            editable_value[0] = False
            self.assertFalse(bridge.editable(object()))
        self.assertIn("AXWindowNumber", queried)
        self.assertIn("AXEditable", queried)


if __name__ == "__main__":
    unittest.main()
