#!/usr/bin/env python3
"""Validate a synthetic Engram memory record."""

from __future__ import annotations

import json
import sys
from pathlib import Path


VALID_TYPES = {"decision", "observation", "reflection", "source_note", "repair"}
VALID_SOURCE_KINDS = {"commit", "file", "diff", "tag", "external"}


def fail(message: str) -> int:
    print(f"ENGRAM_MEMORY_RECORD_INVALID: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: validate_memory_record.py path/to/record.json")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not str(data.get("record_id", "")).startswith("record_"):
        return fail("record_id must start with record_")
    if data.get("record_type") not in VALID_TYPES:
        return fail("record_type is not recognized")
    if not isinstance(data.get("summary"), str) or not data["summary"].strip():
        return fail("summary is required")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        return fail("provenance is required")
    if provenance.get("source_kind") not in VALID_SOURCE_KINDS:
        return fail("provenance.source_kind is not recognized")
    if not provenance.get("version_pointer"):
        return fail("provenance.version_pointer is required")

    confidence = data.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return fail("confidence must be between 0 and 1")

    print("ENGRAM_MEMORY_RECORD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
