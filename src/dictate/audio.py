"""Default-device, in-memory 16 kHz mono signed-16-bit PCM capture."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class _InputStream(Protocol):
	def start(self) -> None: ...
	def stop(self) -> None: ...
	def close(self) -> None: ...


class Recorder:
	"""Capture one utterance in RAM; no audio is written to disk."""

	def __init__(self, device: str = "system-default", stream_factory: Callable[..., _InputStream] | None = None) -> None:
		self._device = None if device == "system-default" else device
		self._stream_factory = stream_factory or self._sounddevice_stream
		self._stream: _InputStream | None = None
		self._frames = bytearray()

	@staticmethod
	def _sounddevice_stream(**kwargs: object) -> _InputStream:
		import sounddevice

		return sounddevice.RawInputStream(**kwargs)

	def start(self) -> None:
		if self._stream is not None:
			raise RuntimeError("recording is already active")
		self._frames.clear()
		self._stream = self._stream_factory(
			samplerate=16_000,
			channels=1,
			dtype="int16",
			device=self._device,
			callback=self._on_audio,
		)
		self._stream.start()

	def _on_audio(self, indata: object, frames: int, time_info: object, status: object) -> None:
		if status:
			raise RuntimeError("audio capture reported a device status")
		self._frames.extend(bytes(indata))

	def stop(self) -> bytes:
		stream, self._stream = self._stream, None
		if stream is None:
			raise RuntimeError("recording is not active")
		try:
			stream.stop()
		finally:
			stream.close()
		audio = bytes(self._frames)
		self._frames.clear()
		return audio

	def discard(self) -> None:
		self._frames.clear()


@dataclass(frozen=True)
class AudioInputDevice:
	identifier: str
	name: str


def list_input_devices(query_devices: Callable[[], object] | None = None) -> tuple[AudioInputDevice, ...]:
	if query_devices is None:
		import sounddevice
		query_devices = sounddevice.query_devices
	devices = query_devices()
	return tuple(AudioInputDevice(str(index), str(device["name"])) for index, device in enumerate(devices) if device.get("max_input_channels", 0) > 0)


def microphone_available(preference: str, devices: tuple[AudioInputDevice, ...]) -> bool:
	return bool(devices) if preference == "system-default" else any(device.identifier == preference for device in devices)


