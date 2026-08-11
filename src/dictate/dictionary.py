"""Newline-delimited local vocabulary loading and deterministic merging."""

from __future__ import annotations

from pathlib import Path

MAX_TERMS = 128
MAX_TERM_LENGTH = 120


def global_dictionary_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".config" / "dictate" / "dictionary.txt"


def project_dictionary_path(project_root: Path) -> Path:
    return project_root / ".dictate" / "dictionary.txt"


def load_dictionary(path: Path) -> dict[str, str]:
    """Return normalized spelling keys mapped to their user-authored spelling."""
    if not path.exists():
        return {}
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        term = raw.strip()
        if not term:
            continue
        if "\x00" in term:
            raise ValueError(f"dictionary contains an invalid term on line {line_number}")
        entries[term.casefold()] = term
    return entries


def merge_dictionaries(global_terms: dict[str, str], project_terms: dict[str, str] | None = None) -> tuple[str, ...]:
    """Merge global terms first; project terms override matching spellings."""
    merged = dict(global_terms)
    merged.update(project_terms or {})
    return tuple(merged[key] for key in sorted(merged) if len(merged[key]) <= MAX_TERM_LENGTH)[:MAX_TERMS]


def terms_for_paths(global_path: Path, project_root: Path | None = None) -> tuple[str, ...]:
    """Load a bounded, deterministic session snapshot; project spellings take precedence."""
    project = load_dictionary(project_dictionary_path(project_root)) if project_root else None
    return merge_dictionaries(load_dictionary(global_path), project)

