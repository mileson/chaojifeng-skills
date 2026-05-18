#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import os
from pathlib import Path

MANAGED_BY = "managed-by: offboarding-handover"


def sync_markdown_agents(src_dir: Path, dst_dir: Path) -> tuple[list[str], list[str], list[str]]:
    dst_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    for src in sorted(src_dir.glob("offboarding-*.md")):
        dst = dst_dir / src.name
        src_text = src.read_text()
        if not dst.exists():
            shutil.copy2(src, dst)
            created.append(src.name)
            continue
        dst_text = dst.read_text()
        if MANAGED_BY not in dst_text:
            skipped.append(src.name)
            continue
        if dst_text != src_text:
            dst.write_text(src_text)
            updated.append(src.name)
    return created, updated, skipped


def sync_toml_agents(src_dir: Path, dst_dir: Path) -> tuple[list[str], list[str], list[str]]:
    dst_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    for src in sorted(src_dir.glob("offboarding-*.toml")):
        dst = dst_dir / src.name
        src_text = src.read_text()
        if not dst.exists():
            shutil.copy2(src, dst)
            created.append(src.name)
            continue
        dst_text = dst.read_text()
        if MANAGED_BY not in dst_text:
            skipped.append(src.name)
            continue
        if dst_text != src_text:
            dst.write_text(src_text)
            updated.append(src.name)
    return created, updated, skipped


def detect_runtime(mode: str) -> list[str]:
    if mode != "auto":
        return [mode]
    runtimes: list[str] = []
    if os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") or (Path.home() / ".claude" / "settings.json").exists():
        runtimes.append("claude")
    if os.environ.get("CODEX_HOME") or (Path.home() / ".codex" / "agents").exists():
        runtimes.append("codex")
    if not runtimes:
        return ["fallback"]
    if len(runtimes) == 2:
        return ["claude", "codex"]
    return runtimes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync managed offboarding agents into local AI coding environments.")
    parser.add_argument("--runtime", choices=("auto", "claude", "codex", "both"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    runtimes = ["claude", "codex"] if args.runtime == "both" else detect_runtime(args.runtime)
    print("runtimes:", runtimes)

    if "claude" in runtimes:
        created, updated, skipped = sync_markdown_agents(skill_root / "agents", Path.home() / ".claude" / "agents")
        print("[claude] created:", created)
        print("[claude] updated:", updated)
        print("[claude] skipped_non_managed:", skipped)
    if "codex" in runtimes:
        created, updated, skipped = sync_toml_agents(skill_root / "agents" / "codex", Path.home() / ".codex" / "agents")
        print("[codex] created:", created)
        print("[codex] updated:", updated)
        print("[codex] skipped_non_managed:", skipped)
    if runtimes == ["fallback"]:
        print("fallback_only: no Claude/Codex runtime confidently detected; rely on skill instructions and prompt-based coordination.")


if __name__ == "__main__":
    main()
