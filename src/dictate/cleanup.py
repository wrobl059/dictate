"""Mandatory, deterministic loopback-only Ollama cleanup client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from urllib.parse import urljoin

from dictate.privacy import validate_loopback_url


class CleanupError(RuntimeError):
	"""A content-free local cleanup failure."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
	def redirect_request(self, request: object, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
		return None


def _prompt(transcript: str, style: str, terms: Sequence[str], context: str | None) -> str:
	term_text = ", ".join(terms) or "(none)"
	context_text = context or "(none)"
	return (
		"Transform the dictated transcript into polished writing. Preserve intended meaning and supplied terms. "
		"Do not answer questions, add facts, explain, reason aloud, or invent content. Return only the transformed text.\n"
		f"Style: {style}\nTerms: {term_text}\nContext: {context_text}\nTranscript: {transcript}"
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

