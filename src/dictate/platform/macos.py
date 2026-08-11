"""Fail-closed macOS microphone and Accessibility integration."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from dictate.platform.base import AcquisitionResult, Capability, PlatformAdapter, TargetSnapshot
from dictate.platform.generic import PynputHotkey

_MICROPHONE_REMEDIATION = "grant Microphone access to the app running Dictate in System Settings > Privacy & Security > Microphone"
_ACCESSIBILITY_REMEDIATION = "grant Accessibility permission to the app running Dictate in System Settings > Privacy & Security > Accessibility"
_SLACK_APPLICATION_TITLE = "slack"


class _AccessibilityBridge(Protocol):
    def trusted(self) -> bool: ...
    def focused_target(self) -> tuple[object, object, object] | None: ...
    def application_id(self, application: object) -> str | None: ...
    def application_title(self, application: object) -> str | None: ...
    def window_id(self, window: object) -> str | None: ...
    def editable(self, element: object) -> bool: ...
    def same(self, first: object, second: object) -> bool: ...
    def replace_selected_text(self, element: object, text: str) -> bool: ...


def write_unicode_keyboard_text(
    text: str,
    *,
    event_factory: Callable[[object, int, bool], object] | None = None,
    unicode_setter: Callable[[object, int, str], None] | None = None,
    event_poster: Callable[[int, object], None] | None = None,
    event_tap: int | None = None,
) -> None:
    """Post a direct Unicode key-down/key-up pair without using the clipboard."""
    if not text:
        return
    if event_factory is None or unicode_setter is None or event_poster is None:
        from Quartz import (  # type: ignore[import-not-found]
            CGEventCreateKeyboardEvent,
            CGEventKeyboardSetUnicodeString,
            CGEventPost,
        )
        event_factory = event_factory or CGEventCreateKeyboardEvent
        unicode_setter = unicode_setter or CGEventKeyboardSetUnicodeString
        event_poster = event_poster or CGEventPost
    utf16_length = len(text.encode("utf-16-le")) // 2
    key_down, key_up = event_factory(None, 0, True), event_factory(None, 0, False)
    unicode_setter(key_down, utf16_length, text)
    unicode_setter(key_up, utf16_length, text)
    if event_tap is None:
        from Quartz import kCGHIDEventTap  # type: ignore[import-not-found]

        event_tap = kCGHIDEventTap
    event_poster(event_tap, key_down)
    event_poster(event_tap, key_up)


class _PyObjCAccessibility:
    """Minimal lazy wrapper around the native Accessibility APIs."""

    def __init__(self) -> None:
        from ApplicationServices import (  # type: ignore[import-not-found]
            AXIsProcessTrusted,
            AXUIElementCopyAttributeValue,
            AXUIElementCreateSystemWide,
            AXUIElementGetPid,
            AXUIElementSetAttributeValue,
            kAXFocusedApplicationAttribute,
            kAXFocusedUIElementAttribute,
            kAXFocusedWindowAttribute,
            kAXRoleAttribute,
            kAXSelectedTextAttribute,
            kAXTextAreaRole,
            kAXTextFieldRole,
        )
        self._trusted = AXIsProcessTrusted
        self._copy = AXUIElementCopyAttributeValue
        self._system_wide = AXUIElementCreateSystemWide
        self._pid = AXUIElementGetPid
        self._set = AXUIElementSetAttributeValue
        # PyObjC 12 does not expose these two constants, although the native
        # Accessibility attribute keys are stable CFStrings.
        self._editable = "AXEditable"
        self._focused_application = kAXFocusedApplicationAttribute
        self._focused_element = kAXFocusedUIElementAttribute
        self._focused_window = kAXFocusedWindowAttribute
        self._role = kAXRoleAttribute
        self._selected_text = kAXSelectedTextAttribute
        self._title = "AXTitle"
        # Browser address bars and web-mail recipient widgets are often exposed
        # as editable combo boxes rather than plain text fields.
        self._text_roles = (kAXTextFieldRole, kAXTextAreaRole, "AXComboBox")
        self._window_number = "AXWindowNumber"

    @staticmethod
    def _value(result: object) -> object | None:
        return result[1] if isinstance(result, tuple) and len(result) == 2 and result[0] == 0 else None  # type: ignore[index]

    def trusted(self) -> bool:
        return bool(self._trusted())

    def focused_target(self) -> tuple[object, object, object] | None:
        system = self._system_wide()
        application = self._value(self._copy(system, self._focused_application, None))
        if application is None:
            return None
        window = self._value(self._copy(application, self._focused_window, None))
        element = self._value(self._copy(system, self._focused_element, None))
        return (application, window, element) if window is not None and element is not None else None

    def application_id(self, application: object) -> str | None:
        result = self._pid(application, None)
        return f"pid:{result[1]}" if isinstance(result, tuple) and len(result) == 2 and result[0] == 0 else None

    def application_title(self, application: object) -> str | None:
        title = self._value(self._copy(application, self._title, None))
        return title if isinstance(title, str) else None

    def window_id(self, window: object) -> str | None:
        number = self._value(self._copy(window, self._window_number, None))
        if isinstance(number, int):
            return f"window:{number}"
        result = self._pid(window, None)
        return f"window-pid:{result[1]}" if isinstance(result, tuple) and len(result) == 2 and result[0] == 0 else None

    def editable(self, element: object) -> bool:
        role = self._value(self._copy(element, self._role, None))
        editable = self._value(self._copy(element, self._editable, None))
        # Browser-backed controls can have composite AX roles, but an explicit
        # AXEditable=True is still a reliable declaration that the focused
        # element accepts text. Native text controls sometimes omit AXEditable.
        # An explicit false always remains read-only.
        return editable is True or (role in self._text_roles and editable is not False)

    def same(self, first: object, second: object) -> bool:
        return first == second

    def replace_selected_text(self, element: object, text: str) -> bool:
        return self._set(element, self._selected_text, text) == 0


def _microphone_authorized() -> bool:
    """Request TCC authorization without opening, sampling, or retaining audio."""
    from AVFoundation import AVCaptureDevice, AVMediaTypeAudio, AVAuthorizationStatusAuthorized, AVAuthorizationStatusNotDetermined  # type: ignore[import-not-found]

    status = AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio)
    if status == AVAuthorizationStatusAuthorized:
        return True
    if status != AVAuthorizationStatusNotDetermined:
        return False
    completed = threading.Event()
    granted = [False]

    def finish(allowed: bool) -> None:
        granted[0] = bool(allowed)
        completed.set()

    AVCaptureDevice.requestAccessForMediaType_completionHandler_(AVMediaTypeAudio, finish)
    return completed.wait(30) and granted[0]


@dataclass(frozen=True)
class _NativeTarget:
    application: object
    window: object
    element: object
    keyboard_input: bool


class MacOSAdapter(PlatformAdapter):
    """Use native authorization and verified Accessibility placement on macOS."""

    def __init__(
        self,
        hotkey_factory: Callable[..., PynputHotkey] = PynputHotkey,
        *,
        microphone_authorized: Callable[[], bool] = _microphone_authorized,
        accessibility_factory: Callable[[], _AccessibilityBridge] = _PyObjCAccessibility,
        text_writer: Callable[[str], None] = write_unicode_keyboard_text,
    ) -> None:
        self._hotkey_factory = hotkey_factory
        self._microphone_authorized = microphone_authorized
        self._accessibility_factory = accessibility_factory
        self._text_writer = text_writer
        self._accessibility: _AccessibilityBridge | None = None
        self._accessibility_unavailable = False
        self._targets: dict[str, _NativeTarget] = {}
        self._hotkey: PynputHotkey | None = None

    def acquire_external_runtime(self, component: str, runner: Callable[[Sequence[str]], bool]) -> AcquisitionResult:
        packages = {"whisper-runtime": "whisper-cpp", "ollama-runtime": "ollama"}
        package = packages.get(component)
        if package is None:
            return AcquisitionResult(False, "unsupported local runtime acquisition")
        try:
            return AcquisitionResult(True) if runner(("brew", "install", package)) else AcquisitionResult(False, "local runtime acquisition failed")
        except PermissionError:
            return AcquisitionResult(False, "grant authorization for local runtime installation")
        except OSError:
            return AcquisitionResult(False, "make local storage and network access available for installation")

    def microphone_permission(self) -> Capability:
        try:
            available = bool(self._microphone_authorized())
            return Capability(available, None if available else _MICROPHONE_REMEDIATION)
        except Exception:
            return Capability(False, _MICROPHONE_REMEDIATION)

    def trigger_permission(self) -> Capability:
        return Capability(True)

    def placement_permission(self) -> Capability:
        bridge = self._bridge()
        try:
            available = bridge is not None and bridge.trusted()
        except Exception:
            available = False
        return Capability(available, None if available else _ACCESSIBILITY_REMEDIATION)

    def context_permission(self) -> Capability:
        return Capability(False, "Accessibility-based destination context is not enabled")

    def snapshot_target(self) -> TargetSnapshot | None:
        bridge = self._trusted_bridge()
        if bridge is None:
            return None
        try:
            focused = bridge.focused_target()
            if focused is None:
                return None
            application, window, element = focused
            application_id, window_id = bridge.application_id(application), bridge.window_id(window)
            if application_id is None or window_id is None or not bridge.editable(element):
                return None
            token = uuid.uuid4().hex
            self._targets[token] = _NativeTarget(
                application, window, element,
                self._requires_keyboard_input(bridge.application_title(application)),
            )
            return TargetSnapshot(application_id, window_id, token)
        except Exception:
            return None

    def read_context(self, target: TargetSnapshot, limit: int) -> str | None:
        return None

    def target_matches(self, target: TargetSnapshot) -> bool:
        bridge, native = self._trusted_bridge(), self._targets.get(target.text_target_id)
        if bridge is None or native is None:
            return False
        try:
            focused = bridge.focused_target()
            if focused is None:
                return False
            application, window, element = focused
            matches = (
                bridge.application_id(application) == target.application_id
                and bridge.window_id(window) == target.window_id
                and bridge.editable(element)
                and bridge.same(application, native.application)
                and bridge.same(window, native.window)
                and bridge.same(element, native.element)
            )
            return matches
        except Exception:
            return False

    def insert_text(self, target: TargetSnapshot, text: str) -> bool:
        if not text or not self.target_matches(target):
            return False
        native, bridge = self._targets.get(target.text_target_id), self._trusted_bridge()
        if native is None or bridge is None:
            return False
        try:
            if native.keyboard_input:
                self._text_writer(text)
                return True
            if bridge.replace_selected_text(native.element, text):
                return True
            return False
        except Exception:
            return False


    @staticmethod
    def _requires_keyboard_input(application_title: str | None) -> bool:
        return application_title is not None and application_title.casefold() == _SLACK_APPLICATION_TITLE


    def release_target(self, target: TargetSnapshot) -> None:
        self._targets.pop(target.text_target_id, None)

    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None:
        self._hotkey = self._hotkey_factory(trigger, on_press, on_release)
        self._hotkey.start()

    def stop_hotkey(self) -> None:
        if self._hotkey is not None:
            self._hotkey.stop()
            self._hotkey = None

    def recovery_instruction(self) -> str:
        return "run dictate serve --recover in this service process"

    def _bridge(self) -> _AccessibilityBridge | None:
        if self._accessibility is None and not self._accessibility_unavailable:
            try:
                self._accessibility = self._accessibility_factory()
            except Exception:
                self._accessibility_unavailable = True
        return self._accessibility

    def _trusted_bridge(self) -> _AccessibilityBridge | None:
        bridge = self._bridge()
        try:
            return bridge if bridge is not None and bridge.trusted() else None
        except Exception:
            return None
