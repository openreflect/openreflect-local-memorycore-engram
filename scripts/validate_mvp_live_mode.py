#!/usr/bin/env python3
"""Validate backend-mode dispatch: fixture default and live-local QMD wiring.

This check runs the CLI against a synthetic stub qmd executable created in a
temporary directory. It is deterministic and public-safe: it does not call the
real QMD CLI, Lossless-Claw, Burrow, OpenClaw, or any private index.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402


STUB_QMD = """#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
if "search" in args:
    print(json.dumps([{"file": "stub-corpus/alpha.md", "snippet": "stub alpha snippet", "score": 0.9}]))
elif "multi-get" in args:
    pointer = args[args.index("multi-get") + 1]
    print(json.dumps([{"file": pointer, "content": "stub alpha content"}]))
else:
    print("stub qmd ok")
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_cli(args: list[str], env_overrides: dict[str, str], audit_log: Path, *, expect_ok: bool = True) -> dict[str, Any]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("MEMORYCORE_")}
    env.update(env_overrides)
    completed = subprocess.run(
        [sys.executable, "-m", "memorycore.cli", "--audit-log", str(audit_log), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_ok and completed.returncode != 0:
        raise ValueError(f"CLI {' '.join(args)} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    if not expect_ok and completed.returncode == 0:
        raise ValueError(f"CLI {' '.join(args)} unexpectedly succeeded")
    return json.loads(completed.stdout)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = Path(tmpdir) / "audit.jsonl"
            stub_bin = Path(tmpdir) / "qmd-stub"
            stub_bin.write_text(STUB_QMD, encoding="utf-8")
            stub_bin.chmod(stub_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            live_env = {
                "MEMORYCORE_BACKEND_MODE": "live-local",
                "MEMORYCORE_QMD_BIN": str(stub_bin),
                "MEMORYCORE_QMD_COLLECTION": "stub-collection",
            }

            # Default mode stays fixture: no env, fixture recall mode.
            fixture_search = run_cli(["search", "alpha-river-contract-fixture"], {}, audit_log)
            require(
                fixture_search["results"][0]["recall_mode"] == "qmd_fixture",
                "default mode should stay fixture",
            )

            # Live-local search routes through the stub subprocess.
            live_search = run_cli(["search", "alpha", "--backend", "qmd"], live_env, audit_log)
            require(live_search["status"] == "ok", "live-local search should succeed")
            require(
                live_search["results"][0]["recall_mode"] == "qmd_live_local",
                "live-local search should use the live adapter",
            )
            require(
                live_search["results"][0]["pointer"]["pointer_id"] == "stub-corpus/alpha.md",
                "live-local search pointer changed",
            )
            require(
                live_search["results"][0]["verification_state"] == "unknown",
                "live search must not overclaim verification",
            )

            # Live-local get resolves the pointer and marks it verified.
            live_get = run_cli(["get", "stub-corpus/alpha.md", "--backend", "qmd"], live_env, audit_log)
            require(live_get["status"] == "ok", "live-local get should succeed")
            require(
                live_get["results"][0]["recall_mode"] == "qmd_live_local",
                "live-local get should use the live adapter",
            )
            require(live_get["verification_state"] == "verified", "resolved live get should verify")

            # Missing QMD binary: backend reports unavailable, structured error.
            missing_bin_env = {**live_env, "MEMORYCORE_QMD_BIN": str(Path(tmpdir) / "no-such-qmd")}
            health = run_cli(["health"], missing_bin_env, audit_log)
            qmd_health = next(item for item in health["results"] if item["backend_id"] == "qmd")
            require(qmd_health["health"] == "unavailable", "missing binary should mark qmd unavailable")
            unavailable = run_cli(["search", "alpha", "--backend", "qmd"], missing_bin_env, audit_log, expect_ok=False)
            require(
                unavailable["error"]["category"] == "backend_unavailable",
                "missing binary search should be backend_unavailable",
            )

            # Missing collection config: unavailable with a config message.
            no_collection_env = {key: value for key, value in live_env.items() if key != "MEMORYCORE_QMD_COLLECTION"}
            no_collection = run_cli(["search", "alpha", "--backend", "qmd"], no_collection_env, audit_log, expect_ok=False)
            require(
                "MEMORYCORE_QMD_COLLECTION" in no_collection["error"]["message"],
                "missing collection should name the config gap",
            )

            # LCM has no host bridge on this surface: unavailable, never fixture fallback.
            lcm = run_cli(["search", "handoff", "--backend", "lossless_claw"], live_env, audit_log, expect_ok=False)
            require(
                lcm["error"]["category"] == "backend_unavailable",
                "live-local LCM should be unavailable without a bridge",
            )

            # Unsupported mode values fail loudly.
            bogus = run_cli(["health"], {"MEMORYCORE_BACKEND_MODE": "bogus"}, audit_log, expect_ok=False)
            require(bogus["error"]["code"] == "CLI_ERROR", "unsupported mode should fail as CLI error")

            # Audit records from live-mode calls stay content-sparse.
            for line in audit_log.read_text(encoding="utf-8").splitlines():
                assert_public_safe(json.loads(line))

    except (json.JSONDecodeError, KeyError, StopIteration, ValueError) as exc:
        print(f"MEMORYCORE_LIVE_MODE_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_LIVE_MODE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
