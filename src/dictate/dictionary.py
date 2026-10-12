"""Newline-delimited local vocabulary loading and deterministic merging."""

from __future__ import annotations

import os
import tempfile
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
    line_numbers: dict[str, int] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        term = raw.strip()
        if not term:
            continue
        if "\x00" in term:
            raise ValueError(f"dictionary contains an invalid term on line {line_number}")
        normalized = term.casefold()
        if normalized in entries:
            raise ValueError(f"dictionary contains duplicate terms on lines {line_numbers[normalized]} and {line_number}")
        entries[normalized] = term
        line_numbers[normalized] = line_number
    return entries


def add_dictionary_term(path: Path, term: str) -> None:
    """Add one valid spelling while retaining the dictionary's existing order."""
    entries = load_dictionary(path)
    term = _validate_term(term, enforce_length=True)
    if term.casefold() in entries:
        raise ValueError("dictionary already contains that term")
    save_dictionary(path, (*entries.values(), term))


def remove_dictionary_term(path: Path, term: str) -> bool:
    """Remove one spelling case-insensitively, returning whether it was present."""
    entries = load_dictionary(path)
    term = _validate_term(term, enforce_length=False)
    if term.casefold() not in entries:
        return False
    del entries[term.casefold()]
    save_dictionary(path, tuple(entries.values()))
    return True


def save_dictionary(path: Path, terms: tuple[str, ...]) -> None:
    """Persist valid terms atomically so a partial edit cannot corrupt vocabulary."""
    normalized: set[str] = set()
    validated: list[str] = []
    for term in terms:
        term = _validate_term(term, enforce_length=False)
        key = term.casefold()
        if key in normalized:
            raise ValueError("dictionary contains duplicate terms")
        normalized.add(key)
        validated.append(term)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            if validated:
                file.write("\n".join(validated) + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def merge_dictionaries(global_terms: dict[str, str], project_terms: dict[str, str] | None = None) -> tuple[str, ...]:
    """Merge global terms first; project terms override matching spellings."""
    merged = dict(global_terms)
    merged.update(project_terms or {})
    return tuple(merged[key] for key in sorted(merged) if len(merged[key]) <= MAX_TERM_LENGTH)[:MAX_TERMS]


def terms_for_paths(global_path: Path, project_root: Path | None = None) -> tuple[str, ...]:
    """Load a bounded, deterministic session snapshot; project spellings take precedence."""
    project = load_dictionary(project_dictionary_path(project_root)) if project_root else None
    return merge_dictionaries(load_dictionary(global_path), project)


def _validate_term(term: str, *, enforce_length: bool) -> str:
    if not isinstance(term, str):
        raise ValueError("dictionary term must be text")
    if "\x00" in term or "\n" in term or "\r" in term:
        raise ValueError("dictionary term contains an invalid character")
    term = term.strip()
    if not term:
        raise ValueError("dictionary term must not be empty")
    if enforce_length and len(term) > MAX_TERM_LENGTH:
        raise ValueError(f"dictionary term must be at most {MAX_TERM_LENGTH} characters")
    return term
