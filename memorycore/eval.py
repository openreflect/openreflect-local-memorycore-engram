"""Public-safe eval runner for the MemoryCore MVP.

This module orchestrates the existing deterministic validation scripts. It does
not call live QMD, Lossless-Claw, Burrow, OpenClaw, or any private runtime.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class EvalSpec:
    eval_id: str
    command: tuple[str, ...]


PUBLIC_SAFE_EVALS = (
    EvalSpec("ENGRAM_MEMORY_RECORD", ("scripts/validate_memory_record.py", "examples/memory-record.example.json")),
    EvalSpec("MEMORYCORE_PACKET_A", ("scripts/validate_mvp_packet_a.py",)),
    EvalSpec("MEMORYCORE_PACKET_B", ("scripts/validate_mvp_packet_b.py",)),
    EvalSpec("MEMORYCORE_PACKET_C", ("scripts/validate_mvp_packet_c.py",)),
    EvalSpec("MEMORYCORE_ROUTER", ("scripts/validate_mvp_router.py",)),
    EvalSpec("MEMORYCORE_QMD_ADAPTER", ("scripts/validate_mvp_qmd_adapter.py",)),
    EvalSpec("MEMORYCORE_LCM_ADAPTER", ("scripts/validate_mvp_lcm_adapter.py",)),
    EvalSpec("MEMORYCORE_PROVENANCE_LEDGER", ("scripts/validate_mvp_provenance_ledger.py",)),
    EvalSpec("MEMORYCORE_VERIFICATION_STATE", ("scripts/validate_mvp_verification_state.py",)),
    EvalSpec("MEMORYCORE_AUDIT_LOG", ("scripts/validate_mvp_audit_log.py",)),
    EvalSpec("MEMORYCORE_CLI", ("scripts/validate_mvp_cli.py",)),
    EvalSpec("MEMORYCORE_MCP_SURFACE", ("scripts/validate_mvp_mcp_surface.py",)),
    EvalSpec("MEMORYCORE_CONTRACT_SECURITY", ("scripts/validate_mvp_contract_security.py",)),
    EvalSpec("MEMORYCORE_CACHE_ROUTER", ("scripts/validate_mvp_cache_router.py",)),
    EvalSpec("MEMORYCORE_CACHE_API", ("scripts/validate_mvp_cache_api.py",)),
    EvalSpec("MEMORYCORE_LIVE_MODE", ("scripts/validate_mvp_live_mode.py",)),
    EvalSpec("MEMORYCORE_WRITE_THROUGH", ("scripts/validate_mvp_write_through.py",)),
    EvalSpec("MEMORYCORE_REAL_VERIFY", ("scripts/validate_mvp_real_verify.py",)),
    EvalSpec("MEMORYCORE_CALLBACK_DELIVERY", ("scripts/validate_mvp_callback_delivery.py",)),
    EvalSpec("MEMORYCORE_JSONL_BACKEND", ("scripts/validate_mvp_jsonl_backend.py",)),
    EvalSpec("MEMORYCORE_VIEWER", ("scripts/validate_mvp_viewer.py",)),
    EvalSpec("MEMORYCORE_E2E_GOLDEN_PATH", ("scripts/validate_e2e_golden_path.py",)),
)

LOCAL_ONLY_SKIPPED = (
    "MEMORYCORE_QMD_LIVE_BACKEND",
    "MEMORYCORE_LCM_LIVE_BACKEND",
    "MEMORYCORE_OPENCLAW_SMOKE",
)


def run_public_safe_eval() -> dict[str, Any]:
    results = [_run_eval(spec) for spec in PUBLIC_SAFE_EVALS]
    passed = [item["eval_id"] for item in results if item["status"] == "passed"]
    failed = [item for item in results if item["status"] == "failed"]

    return {
        "status": "ok" if not failed else "error",
        "mode": "public-safe",
        "passed_eval_ids": passed,
        "failed_eval_ids": [item["eval_id"] for item in failed],
        "skipped_local_only_eval_ids": list(LOCAL_ONLY_SKIPPED),
        "backend_availability": {
            "qmd": "fixture-only",
            "lossless_claw": "fixture-only",
            "openclaw": "not-run-hard-stop",
        },
        "fixture_corpus_status": _fixture_corpus_status(),
        "audit_records_created": 0,
        "provenance_records_created": 0,
        "results": results,
    }


def _run_eval(spec: EvalSpec) -> dict[str, Any]:
    command = (sys.executable, *spec.command)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "eval_id": spec.eval_id,
        "status": "passed" if completed.returncode == 0 else "failed",
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _fixture_corpus_status() -> dict[str, Any]:
    corpus = ROOT / "fixtures" / "corpus"
    files = sorted(path.relative_to(ROOT).as_posix() for path in corpus.glob("*.md"))
    return {
        "status": "present" if files else "missing",
        "file_count": len(files),
        "files": files,
    }
