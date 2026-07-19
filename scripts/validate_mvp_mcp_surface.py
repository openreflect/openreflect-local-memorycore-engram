#!/usr/bin/env python3
"""Validate EVAL-011 MCP tool surface behavior with static fixtures only.

This check calls the local MCP-shaped contract functions against public-safe
fixtures. It does not start an MCP server and does not call QMD,
Lossless-Claw, Burrow, OpenClaw, or the public-safe eval runner.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.mcp_surface import call_tool, list_tools  # noqa: E402

EXPECTED_TOOLS: dict[str, dict[str, Any]] = {
    "memorycore_search": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"]},
            "intent": {
                "type": "string",
                "enum": ["file_corpus_recall", "transcript_continuity_recall"],
                "default": "file_corpus_recall",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
        },
    },
    "memorycore_get": {
        "required": ["pointer_id"],
        "properties": {
            "pointer_id": {"type": "string", "minLength": 1},
            "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"], "default": "qmd"},
        },
    },
    "memorycore_verify": {
        "required": [],
        "properties": {
            "pointer_id": {"type": "string", "minLength": 1},
            "record_id": {"type": "string", "minLength": 1},
            "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"], "default": "mock_healthy"},
            "state": {
                "type": "string",
                "enum": ["verified", "stale", "missing", "unsupported", "unknown"],
                "default": "verified",
            },
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_health": {
        "required": [],
        "properties": {},
    },
    "memorycore_remember": {
        "required": ["memory_type"],
        "properties": {
            "memory_type": {"type": "string", "enum": ["file_corpus", "transcript", "local", "knowledge", "peer"]},
            "content_ref": {"type": "string", "minLength": 1},
            "content": {"type": "string", "minLength": 1},
            "pointer_id": {"type": "string", "minLength": 1},
            "summary_id": {"type": "string", "minLength": 1},
            "verification": {
                "type": "string",
                "enum": ["verified", "stale", "missing", "unsupported", "unknown"],
                "default": "unknown",
            },
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_recall": {
        "required": [],
        "properties": {
            "record_id": {"type": "string", "minLength": 1},
            "pointer_id": {"type": "string", "minLength": 1},
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_cache_search": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "memory_type": {"type": "string", "enum": ["file_corpus", "transcript", "local", "knowledge", "peer"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_fanout_search": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_flush": {
        "required": [],
        "properties": {
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
    "memorycore_confirm_delivery": {
        "required": ["record_id", "outcome"],
        "properties": {
            "record_id": {"type": "string", "minLength": 1},
            "outcome": {"type": "string", "enum": ["delivered", "failed"]},
            "summary_id": {"type": "string", "minLength": 1},
            "message_id": {"type": "string", "minLength": 1},
            "conversation_id": {"type": "string", "minLength": 1},
            "pointer_id": {"type": "string", "minLength": 1},
            "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
        },
    },
}

CLI_ARGS: dict[str, tuple[str, ...]] = {
    "health": ("health",),
    "search": ("search", "alpha-river-contract-fixture", "--intent", "file_corpus_recall", "--limit", "5"),
    "get": ("get", "fixtures/corpus/project-alpha.md", "--backend", "qmd"),
    "verify": ("verify", "fixtures/corpus/project-alpha.md", "--backend", "mock_healthy", "--state", "verified"),
    "unsupported_verify": ("verify", "fixtures/corpus/project-alpha.md", "--backend", "qmd"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "fixtures" / "mcp" / f"{name}.json").read_text(encoding="utf-8"))


def call_fixture(name: str, audit_log: Path) -> dict[str, Any]:
    fixture = load_fixture(name)
    return call_tool(fixture["tool_name"], fixture["arguments"], audit_log=audit_log)


def run_cli(audit_log: Path, name: str, *, expect_ok: bool = True) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "memorycore.cli", "--audit-log", str(audit_log), *CLI_ARGS[name]],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_ok and completed.returncode != 0:
        raise ValueError(f"CLI {name} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    if not expect_ok and completed.returncode == 0:
        raise ValueError(f"CLI {name} unexpectedly succeeded")
    return json.loads(completed.stdout)


def assert_tool_descriptors() -> None:
    tools = {tool["name"]: tool for tool in list_tools()}
    require(set(tools) == set(EXPECTED_TOOLS), "MCP tool names changed")

    for name, expected in EXPECTED_TOOLS.items():
        schema = tools[name]["input_schema"]
        require(schema["type"] == "object", f"{name} schema type changed")
        require(schema.get("additionalProperties") is False, f"{name} should reject unknown arguments")
        require(schema.get("required", []) == expected["required"], f"{name} required arguments changed")
        require(schema.get("properties", {}) == expected["properties"], f"{name} argument properties changed")


def assert_cli_mcp_equivalent(name: str, cli_result: dict[str, Any], mcp_result: dict[str, Any]) -> None:
    cli_core = core_result(cli_result)
    mcp_core = core_result(mcp_result)
    require(cli_core == mcp_core, f"{name} CLI/MCP normalized core result diverged")


def core_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"request_id", "audit_id"}}


def assert_content_sparse_audit(path: Path, expected_count: int, surface: str) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require(len(records) == expected_count, f"{surface} routed calls should append audit records")
    for record in records:
        require(record["client_surface"] == surface, f"audit should preserve {surface} client surface")
        serialized = json.dumps(record, sort_keys=True)
        for private_field in ['"snippet"', '"content"', '"citations"', '"summary"', '"answer"', '"text"']:
            require(private_field not in serialized, f"{surface} audit leaked private field {private_field}")
    return records


def main() -> int:
    try:
        assert_tool_descriptors()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = Path(tmpdir) / "mcp-audit.jsonl"
            cli_audit_log = Path(tmpdir) / "cli-audit.jsonl"

            health = call_fixture("health", audit_log)
            cli_health = run_cli(cli_audit_log, "health")
            assert_cli_mcp_equivalent("health", cli_health, health)
            require(health["status"] == "ok", "health should succeed")
            require({item["backend_id"] for item in health["results"]} >= {"qmd", "lossless_claw", "mock_healthy"}, "health backend list changed")

            search = call_fixture("search", audit_log)
            cli_search = run_cli(cli_audit_log, "search")
            assert_cli_mcp_equivalent("search", cli_search, search)
            require(search["status"] == "ok", "search should succeed")
            require(search["selected_backend"] == "qmd", "search should route to qmd")
            require(search["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "search pointer changed")
            require(search["audit_id"].startswith("audit_"), "search should include audit id")

            get = call_fixture("get", audit_log)
            cli_get = run_cli(cli_audit_log, "get")
            assert_cli_mcp_equivalent("get", cli_get, get)
            require(get["status"] == "ok", "get should succeed")
            require(get["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "get pointer changed")

            verify = call_fixture("verify", audit_log)
            cli_verify = run_cli(cli_audit_log, "verify")
            assert_cli_mcp_equivalent("verify", cli_verify, verify)
            require(verify["status"] == "ok", "verify should succeed")
            require(verify["verification_state"] == "verified", "verify state changed")

            unsupported = call_tool(
                "memorycore_verify",
                {"backend": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
                audit_log=audit_log,
            )
            cli_unsupported = run_cli(cli_audit_log, "unsupported_verify", expect_ok=False)
            assert_cli_mcp_equivalent("unsupported_verify", cli_unsupported, unsupported)
            require(unsupported["status"] == "error", "unsupported verify should fail structurally")
            require(unsupported["error"]["category"] == "verification_unsupported", "unsupported category changed")

            assert_content_sparse_audit(audit_log, 4, "mcp")
            assert_content_sparse_audit(cli_audit_log, 4, "cli")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"MEMORYCORE_MCP_SURFACE_INVALID: {exc}")
        return 1

    print("MEMORYCORE_MCP_SURFACE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
