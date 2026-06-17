#!/usr/bin/env python3
"""Validate EVAL-011 MCP tool surface behavior with static fixtures only.

This check calls the local MCP-shaped contract functions against public-safe
fixtures. It does not start an MCP server and does not call QMD,
Lossless-Claw, Burrow, OpenClaw, or the public-safe eval runner.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.mcp_surface import call_tool, list_tools  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "fixtures" / "mcp" / f"{name}.json").read_text(encoding="utf-8"))


def call_fixture(name: str, audit_log: Path) -> dict[str, Any]:
    fixture = load_fixture(name)
    return call_tool(fixture["tool_name"], fixture["arguments"], audit_log=audit_log)


def main() -> int:
    try:
        tool_names = {tool["name"] for tool in list_tools()}
        require(
            tool_names == {"memorycore_search", "memorycore_get", "memorycore_verify", "memorycore_health"},
            "MCP tool names changed",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = Path(tmpdir) / "mcp-audit.jsonl"

            health = call_fixture("health", audit_log)
            require(health["status"] == "ok", "health should succeed")
            require({item["backend_id"] for item in health["results"]} >= {"qmd", "lossless_claw", "mock_healthy"}, "health backend list changed")

            search = call_fixture("search", audit_log)
            require(search["status"] == "ok", "search should succeed")
            require(search["selected_backend"] == "qmd", "search should route to qmd")
            require(search["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "search pointer changed")
            require(search["audit_id"].startswith("audit_"), "search should include audit id")

            get = call_fixture("get", audit_log)
            require(get["status"] == "ok", "get should succeed")
            require(get["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "get pointer changed")

            verify = call_fixture("verify", audit_log)
            require(verify["status"] == "ok", "verify should succeed")
            require(verify["verification_state"] == "verified", "verify state changed")

            unsupported = call_tool(
                "memorycore_verify",
                {"backend": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
                audit_log=audit_log,
            )
            require(unsupported["status"] == "error", "unsupported verify should fail structurally")
            require(unsupported["error"]["category"] == "verification_unsupported", "unsupported category changed")

            records = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()]
            require(len(records) == 4, "MCP routed calls should append audit records")
            require(records[0]["client_surface"] == "mcp", "audit should preserve MCP client surface")
            for record in records:
                serialized = json.dumps(record, sort_keys=True)
                for private_field in ['"snippet"', '"content"', '"citations"', '"summary"', '"answer"', '"text"']:
                    require(private_field not in serialized, f"audit leaked private field {private_field}")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"MEMORYCORE_MCP_SURFACE_INVALID: {exc}")
        return 1

    print("MEMORYCORE_MCP_SURFACE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
