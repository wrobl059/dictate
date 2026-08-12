"""Mandatory, deterministic loopback-only Ollama cleanup client."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from urllib.parse import urljoin
from urllib.parse import urlparse

from dictate.privacy import validate_loopback_url

_PROFILES = {
	"Natural": "Use clear everyday prose.",
	"Formal": "Use a professional formal tone.",
	"Casual": "Use a conversational but polished tone.",
	"Technical": "Use technically precise terminology and formatting.",
}


class CleanupError(RuntimeError):
	"""A content-free local cleanup failure."""


class OllamaServer:
	"""Own an Ollama process launched for one combined Dictate invocation."""

	def __init__(
		self,
		endpoint: str,
		command: Sequence[str] = ("ollama", "serve"),
		*,
		popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
	) -> None:
		validate_loopback_url(endpoint)
		self.endpoint = endpoint
		self._command = tuple(command)
		self._popen = popen
		self._process: subprocess.Popen[bytes] | None = None

	def start(self) -> None:
		if self._process is not None:
			return
		try:
			endpoint = urlparse(self.endpoint)
			environment = os.environ.copy()
			environment["OLLAMA_HOST"] = f"{endpoint.hostname}:{endpoint.port or 11434}"
			self._process = self._popen(self._command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=environment)
		except OSError as error:
			raise CleanupError("local Ollama runtime could not start") from error

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

	def running(self) -> bool:
		return self._process is not None and self._process.poll() is None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
	def redirect_request(self, request: object, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
		return None


def _prompt(transcript: str, style: str, terms: Sequence[str], context: str | None) -> str:
	if style not in _PROFILES:
		raise CleanupError("unknown writing style")
	term_text = ", ".join(terms) or "(none)"
	context_text = context or "(none)"
	return (
		"Transform the dictated transcript into polished writing while preserving its intended meaning, substantive "
		"wording, emphasis, and supplied terms. Make necessary edits for punctuation, capitalization, grammar, "
		"and dictated formatting. Remove conversational filler, hesitations, repetitions, and abandoned phrasing "
		"when they do not contribute meaning, and resolve explicit false starts or self-corrections. Do not paraphrase, "
		"substitute synonyms, summarize, infer unstated intent, reinterpret, or otherwise change word choice. "
		"Style may affect formatting and tone, not substance. Do not answer questions, add facts, "
		"explain, reason aloud, or invent content. Return only the transformed text.\n"
		f"Style: {style}\nProfile: {_PROFILES[style]}\nTerms: {term_text}\nContext: {context_text}\nTranscript: {transcript}"
	)


class OllamaClient:
	def __init__(self, endpoint: str, model: str, *, opener: Callable[..., object] | None = None) -> None:
		validate_loopback_url(endpoint)
		self.endpoint = endpoint.rstrip("/") + "/"
		self.model = model
		self._opener = opener or urllib.request.build_opener(_NoRedirect()).open

	def ready(self) -> bool:
		validate_loopback_url(self.endpoint)
		payload = {"model": self.model, "prompt": "", "stream": False, "keep_alive": "5m", "options": {"temperature": 0, "num_ctx": 2048}, "think": False}
		try:
			self._request(payload)
		except CleanupError:
			return False
		return True

	def clean(self, transcript: str, style: str, terms: Sequence[str] = (), context: str | None = None) -> str:
		if not transcript.strip():
			raise CleanupError("ASR returned no usable transcription")
		payload = {
			"model": self.model,
			"prompt": _prompt(transcript, style, terms, context),
			"stream": False,
			"think": False,
			"keep_alive": "5m",
			"options": {"temperature": 0, "num_ctx": 2048},
		}
		response = self._request(payload)
		text = response.get("response") if isinstance(response, dict) else None
		if not isinstance(text, str) or not text.strip() or response.get("thinking"):
			raise CleanupError("local cleanup returned no usable output")
		return text.strip()

	def _request(self, payload: dict[str, object]) -> dict[str, object]:
		validate_loopback_url(self.endpoint)
		body = json.dumps(payload).encode("utf-8")
		request = urllib.request.Request(
			urljoin(self.endpoint, "api/generate"), data=body, headers={"Content-Type": "application/json", "Accept": "application/json"}, method="POST"
		)
		try:
			with self._opener(request, timeout=30) as response:
				if not 200 <= response.status < 300:
					raise CleanupError("local cleanup returned an unsuccessful status")
				result = json.loads(response.read().decode("utf-8"))
		except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
			raise CleanupError("local cleanup request failed") from error
		if not isinstance(result, dict):
			raise CleanupError("local cleanup returned an invalid response")
		return result

