"""Bounded, ephemeral context from the original text target only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundedContext:
	selection: str = ""
	nearby_text: str = ""

	def render(self, limit: int) -> str | None:
		if limit <= 0:
			raise ValueError("context limit must be positive")
		value = "\n".join(part for part in (self.selection, self.nearby_text) if part)
		return value[:limit] or None

