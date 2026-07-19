#!/usr/bin/env python3
"""Validate the EN-026 operator console: audited controls over config entries.

Exercises the control handlers directly (the HTTP layer is a thin shell):
backend toggles produce honest BACKEND_DISABLED errors and receipts; routing
edits change flush targets (mirroring via two checks); mode follows
env > config > default precedence; verify-all restamps records; forget
removes the cache row while leaving the audit receipt; and a declared
backend with no installed adapter degrades honestly. Deterministic and
public-safe.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.cli import resolve_backend_mode  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402
from memorycore.viewer import handle_control  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            config_path = tmp / "config.json"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}
            ctl = {"cache_db": cache_db, "audit_log": audit_log, "config_path": config_path}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(tmp / "jsonl-store.jsonl")
            os.environ["MEMORYCORE_CONFIG"] = str(config_path)

            # Defaults: no config file behaves exactly like the built-ins.
            require(resolve_backend_mode() == "fixture", "default mode changed")

            # EN-036: the memory landscape ships declared by default —
            # visible, disabled, honestly adapterless until configured.
            from memorycore.operator_config import DECLARED_BY_DEFAULT, describe_backends, load_config
            defaults = {b["backend_id"]: b for b in describe_backends(load_config(config_path))}
            for declared_id in ("agentcore_memory", "mem0", "zep", "letta", "honcho"):
                require(declared_id in defaults, f"{declared_id} missing from default declarations")
                entry = defaults[declared_id]
                require(entry["enabled"] is False, f"{declared_id} must ship disabled")
                require(entry["adapter_installed"] is False, f"{declared_id} must be honest about no adapter")
                require(entry["description"] and entry["url"], f"{declared_id} needs description and docs url")
            require(set(DECLARED_BY_DEFAULT) <= set(defaults), "declared set drifted from defaults")

            # EN-037: vertex graduated to an installed adapter but stays
            # disabled by default — it is a remote service, and content
            # leaves the machine only by explicit operator choice.
            require(defaults["vertex_memory_bank"]["adapter_installed"] is True, "vertex adapter should be installed")
            require(defaults["vertex_memory_bank"]["enabled"] is False, "vertex must still ship disabled")

            # Toggle jsonl_store off: writes are refused honestly, with a receipt.
            out = handle_control("backend", {"backend_id": "jsonl_store", "enabled": False}, **ctl)
            require(out["status"] == "ok", "backend toggle failed")
            refused = call_tool("memorycore_remember", {"memory_type": "local", "content": "should not land"}, **kwargs)
            require(refused["status"] == "error", "disabled backend accepted a write")
            require(refused["error"]["code"] == "BACKEND_DISABLED", "disable error code changed")

            # Re-enable: writes work again.
            handle_control("backend", {"backend_id": "jsonl_store", "enabled": True}, **ctl)
            written = call_tool("memorycore_remember", {"memory_type": "local", "content": "console memory alpha"}, **kwargs)
            require(written["status"] == "ok", "re-enabled backend refused a write")
            record_id = written["results"][0]["record_id"]

            # Routing edit: two targets on one row means mirrored flush.
            out = handle_control("routing", {"memory_type": "local", "backends": ["jsonl_store", "qmd"]}, **ctl)
            require(out["status"] == "ok", "routing change failed")
            pointer_only = call_tool(
                "memorycore_remember",
                {"memory_type": "local", "content_ref": "jsonl://memorycore/pointer-only-fixture"},
                **kwargs,
            )
            require(pointer_only["results"][0]["flush_state"] == "pending", "pointer remember should be pending")
            flushed = call_tool("memorycore_flush", {}, **kwargs)
            states = {r["record_id"]: r["flush_state"] for r in flushed["results"]}
            require(states.get(pointer_only["results"][0]["record_id"]) == "mirrored", "two-target routing should mirror")

            # Undeclared backend and unknown action are rejected.
            require(handle_control("routing", {"memory_type": "local", "backends": ["nope"]}, **ctl)["status"] == "error",
                    "undeclared backend accepted")
            require(handle_control("bogus", {}, **ctl)["status"] == "error", "unknown action accepted")

            # Mode precedence: config wins when env is unset; env wins when set.
            handle_control("mode", {"mode": "live-local"}, **ctl)
            require(resolve_backend_mode() == "live-local", "config mode not honored")
            os.environ["MEMORYCORE_BACKEND_MODE"] = "fixture"
            require(resolve_backend_mode() == "fixture", "env override should win")
            del os.environ["MEMORYCORE_BACKEND_MODE"]
            handle_control("mode", {"mode": "fixture"}, **ctl)

            # Verify-all restamps records (jsonl verification is real in every mode).
            out = handle_control("verify_all", {}, **ctl)
            require(out["status"] == "ok" and "verified" in out["message"], "verify_all should verify jsonl records")

            # Forget: cache row gone, receipt remains.
            out = handle_control("forget", {"record_id": record_id}, **ctl)
            require(out["status"] == "ok", "forget failed")
            miss = call_tool("memorycore_recall", {"record_id": record_id}, **kwargs)
            require(miss["status"] == "error" and miss["error"]["code"] == "CACHE_MISS", "forgotten record still recalled")
            require(handle_control("forget", {"record_id": record_id}, **ctl)["status"] == "error",
                    "double forget should fail")

            # Declared-but-not-installed backend degrades honestly.
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["backends"]["honcho"] = {"enabled": True, "class": "peer_reasoning", "display_name": "Honcho"}
            config["routing"]["local"] = ["honcho"]
            config_path.write_text(json.dumps(config), encoding="utf-8")
            from memorycore.operator_config import describe_backends, load_config
            described = {b["backend_id"]: b for b in describe_backends(load_config(config_path))}
            require(described["honcho"]["adapter_installed"] is False, "future backend should show no adapter")
            routed = call_tool(
                "memorycore_remember",
                {"memory_type": "local", "content_ref": "jsonl://memorycore/future-routed"},
                **kwargs,
            )
            require(routed["results"][0]["pointer"]["backend_id"] == "honcho", "declared backend should be routable")
            failed = call_tool("memorycore_flush", {}, **kwargs)
            fstates = {r["record_id"]: r["flush_state"] for r in failed["results"]}
            require(fstates.get(routed["results"][0]["record_id"]) == "failed", "no-adapter flush must fail honestly")

            # Restore local routing, then exercise reveal / declare / pack.
            handle_control("routing", {"memory_type": "local", "backends": ["jsonl_store"]}, **ctl)
            secret = "reveal target: the console demonstrated its own receipt."
            revealable = call_tool("memorycore_remember", {"memory_type": "local", "content": secret}, **kwargs)
            reveal_id = revealable["results"][0]["record_id"]

            out = handle_control("reveal", {"record_id": reveal_id}, **ctl)
            require(out["status"] == "ok" and out["content"] == secret, "reveal should return backend content")
            require(out["hash_match"] is True, "healthy reveal should hash-match")

            store_path = Path(os.environ["MEMORYCORE_JSONL_STORE"])
            lines = store_path.read_text(encoding="utf-8").splitlines()
            tampered = []
            for line in lines:
                obj = json.loads(line)
                if secret in obj.get("content", ""):
                    obj["content"] = obj["content"] + " [tampered]"
                tampered.append(json.dumps(obj, sort_keys=True, separators=(",", ":")))
            store_path.write_text("\n".join(tampered) + "\n", encoding="utf-8")
            out = handle_control("reveal", {"record_id": reveal_id}, **ctl)
            require(out["hash_match"] is False, "tampered reveal must expose the mismatch")

            require(handle_control("declare", {"backend_id": "notion_probe", "display_name": "Notion Probe", "class": "provenance_fabric"}, **ctl)["status"] == "ok",
                    "declare should accept a reserved-class backend")
            require(handle_control("declare", {"backend_id": "notion_probe", "class": "provenance_fabric"}, **ctl)["status"] == "error",
                    "duplicate declare should be rejected")
            require(handle_control("declare", {"backend_id": "bad", "class": "made_up"}, **ctl)["status"] == "error",
                    "unknown class should be rejected")
            require(handle_control("declare", {"backend_id": "Bad-Slug!", "class": "knowledge_brain"}, **ctl)["status"] == "error",
                    "invalid slug should be rejected")
            declared_now = {b["backend_id"]: b for b in describe_backends(load_config(config_path))}
            require(declared_now["notion_probe"]["enabled"] is False, "declared backends must start disabled")

            out = handle_control("pack", {"record_id": reveal_id}, **ctl)
            require(out["status"] == "ok" and out["integrity"], "pack export should succeed with integrity hash")
            require(reveal_id in out["human_readable"], "pack should name the record")
            require(secret not in json.dumps(out["pack"]), "pack must stay content-sparse")

            # GAP-010: content search maps memory content to cache records.
            from memorycore.viewer import content_search_matches
            matches = content_search_matches(cache_db, "console demonstrated")
            require(len(matches) == 1 and matches[0]["record_id"] == reveal_id,
                    "content search should link content to the cache record")
            require("receipt" in matches[0]["snippet"], "content match should carry a snippet")
            require(content_search_matches(cache_db, "xy") == [], "short queries should return nothing")

            # GAP-009: reset_config is the escape hatch from half-applied state.
            # Current state is deliberately dirty: routing local -> honcho,
            # declared backends honcho + gbrain, from the tests above.
            out = handle_control("reset_config", {}, **ctl)
            require(out["status"] == "ok", "reset_config failed")
            reset_cfg = load_config(config_path)
            require(reset_cfg["routing"]["local"] == ["jsonl_store"], "reset should restore default routing")
            require(reset_cfg["mode"] == "fixture", "reset should restore fixture mode")
            require(all(reset_cfg["backends"][b]["enabled"] for b in ("jsonl_store", "qmd", "lossless_claw", "gbrain")),
                    "reset should enable installed backends")
            require(reset_cfg["backends"]["vertex_memory_bank"]["enabled"] is False,
                    "reset must keep the remote vertex backend disabled")
            require("honcho" in reset_cfg["backends"] and reset_cfg["backends"]["honcho"]["enabled"] is False,
                    "reset must preserve declared backends, disabled")
            require("notion_probe" in reset_cfg["backends"] and reset_cfg["backends"]["notion_probe"]["enabled"] is False,
                    "reset must preserve notion_probe declared, disabled")

            # Every control action left a content-sparse receipt.
            records = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()]
            ui_records = [r for r in records if r["client_surface"] == "operator_ui"]
            actions = {r.get("config_change", {}).get("action") for r in ui_records}
            require({"backend_toggle", "routing_change", "mode_change", "verify_all", "forget",
                     "reveal", "declare_backend", "pack_export", "config_reset"} <= actions,
                    f"missing control receipts: {actions}")
            for record in records:
                assert_public_safe(record)
            require(secret not in audit_log.read_text(encoding="utf-8"), "revealed content leaked into audit")
            require("should not land" not in config_path.read_text(encoding="utf-8"), "content leaked into config")

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_OPERATOR_CONSOLE_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_OPERATOR_CONSOLE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
