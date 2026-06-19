#!/usr/bin/env python3
"""Create an isolated public-safe QMD fixture collection.

This script intentionally avoids the operator's default QMD index. It creates
or refreshes a local fixture-only QMD index containing only fixtures/corpus.
Generated QMD state lives under .memorycore/, which is ignored by git.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION = "memorycore-public-fixtures"
DEFAULT_STATE_DIR = ROOT / ".memorycore" / "qmd-public-fixtures"
DEFAULT_CORPUS = ROOT / "fixtures" / "corpus"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--qmd-bin", default=os.environ.get("QMD_BIN", "qmd"))
    parser.add_argument("--recreate", action="store_true", help="Delete and rebuild the isolated fixture index")
    args = parser.parse_args()

    corpus = args.corpus.resolve()
    state_dir = args.state_dir.resolve()
    config_dir = state_dir / "config"
    index_path = state_dir / "index.sqlite"

    if not corpus.is_dir():
        print(f"MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: corpus missing: {corpus}", file=sys.stderr)
        return 2
    if shutil.which(args.qmd_bin) is None:
        print(f"MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: QMD CLI not found: {args.qmd_bin}", file=sys.stderr)
        return 2

    if args.recreate and state_dir.exists():
        shutil.rmtree(state_dir)

    config_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["QMD_CONFIG_DIR"] = str(config_dir)
    env["INDEX_PATH"] = str(index_path)

    add = _run(
        [
            args.qmd_bin,
            "collection",
            "add",
            str(corpus),
            "--name",
            args.collection,
            "--mask",
            "**/*.md",
        ],
        env=env,
    )
    if add.returncode != 0:
        combined = f"{add.stdout}\n{add.stderr}".lower()
        if "already exists" not in combined:
            print("MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: qmd collection add failed", file=sys.stderr)
            _print_process(add)
            return 2

    update = _run([args.qmd_bin, "update"], env=env)
    if update.returncode != 0:
        print("MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: qmd update failed", file=sys.stderr)
        _print_process(update)
        return 2

    search = _run(
        [
            args.qmd_bin,
            "search",
            "--json",
            "-n",
            "1",
            "-c",
            args.collection,
            "alpha river contract fixture",
        ],
        env=env,
    )
    if search.returncode != 0:
        print("MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: qmd fixture search failed", file=sys.stderr)
        _print_process(search)
        return 2
    try:
        search_results = json.loads(search.stdout)
    except json.JSONDecodeError:
        search_results = []
    if not search_results:
        print("MEMORYCORE_QMD_FIXTURE_COLLECTION_BLOCKED: qmd fixture search returned no results", file=sys.stderr)
        return 2

    print("MEMORYCORE_QMD_FIXTURE_COLLECTION_OK")
    print(f"collection={args.collection}")
    print(f"corpus={corpus}")
    print(f"QMD_CONFIG_DIR={config_dir}")
    print(f"INDEX_PATH={index_path}")
    print("validate_command:")
    print(
        "  "
        f"QMD_CONFIG_DIR={_shell(config_dir)} "
        f"INDEX_PATH={_shell(index_path)} "
        f"python3 scripts/validate_local_qmd_adapter.py --collection {args.collection}"
    )
    return 0


def _run(command: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _print_process(process: subprocess.CompletedProcess[str]) -> None:
    if process.stdout.strip():
        print(process.stdout.strip(), file=sys.stderr)
    if process.stderr.strip():
        print(process.stderr.strip(), file=sys.stderr)


def _shell(path: Path) -> str:
    return "'" + str(path).replace("'", "'\\''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
