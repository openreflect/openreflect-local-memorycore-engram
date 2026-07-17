"""Operator configuration for the MemoryCore control plane (EN-026).

Backends and routing are config entries, not code constants. The operator
config file declares which memory systems exist, whether each is enabled,
and how memory types route to them. Future systems (peer reasoning,
knowledge brains, fabric substrates) are added by declaring entries — the
control surface renders whatever is declared, and anything declared without
an installed adapter degrades honestly rather than silently.

Precedence for the backend mode: explicit MEMORYCORE_BACKEND_MODE env var
beats the config file, which beats the fixture default — so nothing changes
behavior unless the operator asks it to.

Every config change is written through ``apply_config_change`` so the
settings themselves carry an audit trail (client_surface "operator_ui").
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memorycore.audit_log import append_record, build_audit_record

SCHEMA_VERSION = 1

# Backend classes: the taxonomy future systems land in. Reserved classes are
# part of the contract today even though no adapter ships for them yet.
BACKEND_CLASSES = (
    "local_record",
    "corpus_index",
    "transcript_continuity",
    "peer_reasoning",       # reserved: e.g. Honcho
    "knowledge_brain",      # reserved: e.g. gbrain
    "provenance_fabric",    # reserved: e.g. Notion / Drive / S3 substrates
)

# Adapters that actually exist in this codebase, with their capabilities.
# A config may declare backends beyond this set; they render as
# declared/no-adapter and never receive traffic.
INSTALLED_ADAPTERS: dict[str, dict[str, Any]] = {
    "jsonl_store": {
        "class": "local_record",
        "display_name": "JSONL Store",
        "capabilities": {"read": True, "write_through": True, "verify": "always", "content_search": True},
    },
    "qmd": {
        "class": "corpus_index",
        "display_name": "QMD",
        "capabilities": {"read": True, "write_through": True, "verify": "live-local", "content_search": False},
    },
    "lossless_claw": {
        "class": "transcript_continuity",
        "display_name": "Lossless-Claw (LCM)",
        "capabilities": {"read": True, "write_through": "callback", "verify": "pending", "content_search": False},
    },
}

DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "mode": "fixture",
    "backends": {
        backend_id: {"enabled": True, "class": spec["class"], "display_name": spec["display_name"]}
        for backend_id, spec in INSTALLED_ADAPTERS.items()
    },
    "routing": {
        "local": ["jsonl_store"],
        "file_corpus": ["qmd"],
        "transcript": ["lossless_claw"],
    },
}


def load_config(path: Path) -> dict[str, Any]:
    """Load operator config, merging over defaults; missing file = defaults."""
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        for backend_id, entry in stored.get("backends", {}).items():
            config["backends"].setdefault(backend_id, {})
            config["backends"][backend_id].update(entry)
        config["routing"].update(stored.get("routing", {}))
        if stored.get("mode") in ("fixture", "live-local"):
            config["mode"] = stored["mode"]
        config["updated_at"] = stored.get("updated_at")
    return config


def save_config(path: Path, config: dict[str, Any]) -> None:
    config = dict(config)
    config["schema_version"] = SCHEMA_VERSION
    config["updated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def effective_routing(config: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Routing filtered to enabled backends; empty targets stay explicit."""
    backends = config.get("backends", {})
    routing: dict[str, tuple[str, ...]] = {}
    for memory_type, targets in config.get("routing", {}).items():
        routing[memory_type] = tuple(
            backend_id for backend_id in targets if backends.get(backend_id, {}).get("enabled", False)
        )
    return routing


def backend_enabled(config: dict[str, Any], backend_id: str) -> bool:
    return bool(config.get("backends", {}).get(backend_id, {}).get("enabled", False))


def describe_backends(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Merged operator view: declared entries + installed-adapter reality."""
    described = []
    for backend_id, entry in config.get("backends", {}).items():
        installed = INSTALLED_ADAPTERS.get(backend_id)
        described.append(
            {
                "backend_id": backend_id,
                "display_name": entry.get("display_name", backend_id),
                "class": entry.get("class", "unclassified"),
                "enabled": bool(entry.get("enabled", False)),
                "adapter_installed": installed is not None,
                "capabilities": (installed or {}).get("capabilities", {}),
            }
        )
    return described


def apply_config_change(
    config_path: Path,
    audit_log: Path,
    *,
    action: str,
    detail: dict[str, Any],
    mutate,
) -> dict[str, Any]:
    """Apply a mutation to the config and leave a receipt for the change.

    The audit record is content-sparse: it names the action and structural
    detail (backend ids, memory types, modes), never memory content.
    """
    config = load_config(config_path)
    mutate(config)
    save_config(config_path, config)

    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    request = {
        "request_id": f"req_operator_ui_{action}",
        "client_surface": "operator_ui",
        "operation": "config_change",
        "intent": action,
    }
    result = {"status": "ok", "results": [], "selected_backend": detail.get("backend_id")}
    record = build_audit_record(request, result, timestamp=timestamp)
    record["config_change"] = {"action": action, **detail}
    append_record(audit_log, record)
    return config
