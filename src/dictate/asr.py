"""Supervised localhost whisper.cpp client using in-memory WAV requests."""

from __future__ import annotations

import io
import json
import subprocess
import urllib.error
import urllib.request
import wave
from collections.abc import Callable, Sequence
from urllib.parse import quote, urljoin

from dictate.privacy import PrivacyError, validate_loopback_url


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
		if self._process is not None:
			self._process.terminate()
			self._process = None

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
		request = urllib.request.Request(
			urljoin(self.endpoint, "inference"),
			data=_wav(pcm),
			headers={"Content-Type": "audio/wav", "Accept": "application/json", "X-Whisper-Initial-Prompt": quote(", ".join(terms), safe="")},
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

