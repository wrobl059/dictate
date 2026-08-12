"""Supervised localhost whisper.cpp client using in-memory WAV requests."""

from __future__ import annotations

import io
import json
import subprocess
import urllib.error
import urllib.request
import uuid
import wave
from collections.abc import Callable, Sequence
from urllib.parse import urljoin, urlparse

from dictate.config import Preferences
from dictate.privacy import validate_loopback_url


class ASRError(RuntimeError):
	"""A content-free local ASR failure."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
	def redirect_request(self, request: object, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
		return None


def _wav(pcm: bytes) -> bytes:
	buffer = io.BytesIO()
	with wave.open(buffer, "wb") as output:
		output.setnchannels(1)
		output.setsampwidth(2)
		output.setframerate(16_000)
		output.writeframes(pcm)
	return buffer.getvalue()


def _multipart_wav(pcm: bytes, terms: Sequence[str]) -> tuple[bytes, str]:
	"""Build whisper.cpp's local multipart request without persisting audio."""
	boundary = f"----dictate-{uuid.uuid4().hex}"
	parts = (
		f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode("ascii") + _wav(pcm),
		f'--{boundary}\r\nContent-Disposition: form-data; name="prompt"\r\n\r\n'.encode("ascii") + ", ".join(terms).encode("utf-8"),
		f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\njson'.encode("ascii"),
	)
	return b"\r\n".join(parts) + f"\r\n--{boundary}--\r\n".encode("ascii"), f"multipart/form-data; boundary={boundary}"


def whisper_server_command(preferences: Preferences) -> tuple[str, ...]:
	"""Build the loopback-only command from installer-verified local artifacts."""
	if not preferences.whisper_server_executable or not preferences.whisper_model_path:
		raise ASRError("local ASR runtime and model must be installed")
	endpoint = urlparse(preferences.asr_endpoint)
	validate_loopback_url(preferences.asr_endpoint)
	if endpoint.port is None:
		raise ASRError("local ASR endpoint must include a port")
	return (preferences.whisper_server_executable, "--model", preferences.whisper_model_path, "--host", endpoint.hostname or "127.0.0.1", "--port", str(endpoint.port))


class WhisperServer:
	"""Own one local whisper-server process for the lifetime of a service."""

	def __init__(
		self,
		endpoint: str,
		command: Sequence[str] | None = None,
		*,
		popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
		opener: Callable[..., object] | None = None,
	) -> None:
		validate_loopback_url(endpoint)
		self.endpoint = endpoint.rstrip("/") + "/"
		self._command = tuple(command) if command else None
		self._popen = popen
		self._process: subprocess.Popen[bytes] | None = None
		self._opener = opener or urllib.request.build_opener(_NoRedirect()).open

	def start(self) -> None:
		if self._command is None or self._process is not None:
			return
		try:
			self._process = self._popen(self._command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		except OSError as error:
			raise ASRError("local ASR runtime could not start") from error

	def stop(self) -> None:
		process, self._process = self._process, None
		if process is None or process.poll() is not None:
			return
		try:
			process.terminate()
			wait = getattr(process, "wait", None)
			if wait is not None:
				wait(timeout=3)
		except subprocess.TimeoutExpired:
			kill = getattr(process, "kill", None)
			if kill is None:
				return
			kill()
			try:
				wait = getattr(process, "wait", None)
				if wait is not None:
					wait(timeout=3)
			except subprocess.TimeoutExpired:
				pass
		except OSError:
			pass

	def ready(self) -> bool:
		self._ensure_running()
		request = urllib.request.Request(urljoin(self.endpoint, "health"), method="GET")
		try:
			with self._opener(request, timeout=2) as response:
				return 200 <= response.status < 300
		except (urllib.error.URLError, TimeoutError, OSError):
			return False

	def transcribe(self, pcm: bytes, terms: Sequence[str] = ()) -> str:
		if not pcm:
			raise ASRError("audio capture was empty")
		self._ensure_running()
		validate_loopback_url(self.endpoint)
		body, content_type = _multipart_wav(pcm, terms)
		request = urllib.request.Request(
			urljoin(self.endpoint, "inference"),
			data=body,
			headers={"Content-Type": content_type, "Accept": "application/json"},
			method="POST",
		)
		try:
			with self._opener(request, timeout=30) as response:
				if not 200 <= response.status < 300:
					raise ASRError("local ASR returned an unsuccessful status")
				payload = json.loads(response.read().decode("utf-8"))
		except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
			raise ASRError("local ASR request failed") from error
		text = payload.get("text") if isinstance(payload, dict) else None
		if not isinstance(text, str) or not text.strip():
			raise ASRError("local ASR returned no usable transcription")
		return text.strip()

	def _ensure_running(self) -> None:
		if self._process is not None and self._process.poll() is not None:
			raise ASRError("local ASR runtime stopped unexpectedly")

	def running(self) -> bool:
		"""Report the liveness of a process owned by this client, if any."""
		return self._process is not None and self._process.poll() is None

