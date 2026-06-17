#!/usr/bin/env python3
"""Validate EVAL-010 CLI behavior with static fixtures only.

This check invokes the local CLI against public-safe fixture data and temporary
audit storage. It does not call QMD, Lossless-Claw, Burrow, OpenClaw, or the
public-safe eval runner.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_cli(audit_log: Path, *args: str, expect_ok: bool = True) -> dict[str, Any] | list[dict[str, Any]]:
    command = [sys.executable, "-m", "memorycore.cli", "--audit-log", str(audit_log), *args]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if expect_ok and completed.returncode != 0:
        raise ValueError(f"CLI command failed: {' '.join(args)}\n{completed.stderr}\n{completed.stdout}")
    if not expect_ok and completed.returncode == 0:
        raise ValueError(f"CLI command unexpectedly succeeded: {' '.join(args)}")
    return json.loads(completed.stdout)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = Path(tmpdir) / "audit.jsonl"

            backends = run_cli(audit_log, "list-backends")
            require(backends["status"] == "ok", "list-backends should succeed")
            require({item["backend_id"] for item in backends["results"]} >= {"qmd", "lossless_claw", "mock_healthy"}, "backend list changed")

            health = run_cli(audit_log, "health")
            require(health["operation"] == "health", "health operation changed")

            search = run_cli(audit_log, "search", "alpha-river-contract-fixture")
            require(search["status"] == "ok", "search should succeed")
            require(search["selected_backend"] == "qmd", "search should route to qmd by default")
            require(search["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "search pointer changed")
            require(search["audit_id"].startswith("audit_"), "search should include audit id")

            get = run_cli(audit_log, "get", "fixtures/corpus/project-alpha.md", "--backend", "qmd")
            require(get["status"] == "ok", "get should succeed")
            require(get["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "get pointer changed")

            verify = run_cli(audit_log, "verify", "fixtures/corpus/project-alpha.md", "--backend", "mock_healthy")
            require(verify["status"] == "ok", "verify should succeed")
            require(verify["verification_state"] == "verified", "verify state changed")

            unsupported = run_cli(audit_log, "verify", "fixtures/corpus/project-alpha.md", "--backend", "qmd", expect_ok=False)
            require(unsupported["status"] == "error", "unsupported verify should fail")
            require(unsupported["error"]["category"] == "verification_unsupported", "unsupported category changed")

            recent = run_cli(audit_log, "audit", "--limit", "3")
            require(len(recent) == 3, "audit limit changed")
            require(recent[-1]["request_id"] == "req_cli_verify", "recent audit ordering changed")
            for record in recent:
                serialized = json.dumps(record, sort_keys=True)
                for private_field in ['"snippet"', '"content"', '"citations"', '"summary"', '"answer"', '"text"']:
                    require(private_field not in serialized, f"audit leaked private field {private_field}")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"MEMORYCORE_CLI_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_CLI_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
