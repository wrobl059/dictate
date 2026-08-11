"""Directly editable TOML preferences with safe defaults."""

from __future__ import annotations

import os
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dictate.privacy import validate_loopback_url

STYLES = ("Natural", "Formal", "Casual", "Technical")
DEFAULT_TRIGGER = "right_alt"
DEFAULT_OLLAMA_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_ASR_ENDPOINT = "http://127.0.0.1:8080"
DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


@dataclass(frozen=True)
class Preferences:
    microphone: str = "system-default"
    trigger: str = DEFAULT_TRIGGER
    style: str = "Natural"
    asr_endpoint: str = DEFAULT_ASR_ENDPOINT
    ollama_endpoint: str = DEFAULT_OLLAMA_ENDPOINT
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    context_limit: int = 1_024


def validate_preferences(preferences: Preferences) -> Preferences:
    if not all(isinstance(value, str) for value in (
        preferences.microphone,
        preferences.trigger,
        preferences.style,
        preferences.asr_endpoint,
        preferences.ollama_endpoint,
        preferences.ollama_model,
    )):
        raise ValueError("string preferences must be TOML strings")
    if isinstance(preferences.context_limit, bool) or not isinstance(preferences.context_limit, int):
        raise ValueError("context_limit must be a TOML integer")
    if preferences.microphone == "":
        raise ValueError("microphone must be system-default or a device identifier")
    if not preferences.trigger:
        raise ValueError("trigger must not be empty")
    if preferences.style not in STYLES:
        raise ValueError(f"style must be one of: {', '.join(STYLES)}")
    if preferences.context_limit <= 0:
        raise ValueError("context_limit must be positive")
    validate_loopback_url(preferences.asr_endpoint)
    validate_loopback_url(preferences.ollama_endpoint)
    if not preferences.ollama_model:
        raise ValueError("ollama_model must not be empty")
    return preferences


def load_preferences(path: Path) -> Preferences:
    if not path.exists():
        return validate_preferences(Preferences())
    with path.open("rb") as file:
        data = tomllib.load(file)
    unknown = set(data) - set(Preferences.__dataclass_fields__)
    if unknown:
        raise ValueError(f"unknown preference: {sorted(unknown)[0]}")
    try:
        preferences = Preferences(**data)
    except TypeError as error:
        raise ValueError("invalid preferences TOML") from error
    return validate_preferences(preferences)


def save_preferences(path: Path, preferences: Preferences) -> None:
    preferences = validate_preferences(preferences)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f'{name} = {value!r}' for name, value in vars(preferences).items()) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


