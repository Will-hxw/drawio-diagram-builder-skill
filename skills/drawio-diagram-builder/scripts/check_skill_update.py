#!/usr/bin/env python3
"""Check whether an installed drawio-diagram-builder skill is current."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_VERSION_URL = (
    "https://raw.githubusercontent.com/Will-hxw/drawio-diagram-builder-skill/"
    "main/skills/drawio-diagram-builder/VERSION"
)
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_version(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if not VERSION_RE.match(value):
        raise ValueError(f"invalid semantic version: {value!r}")
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def read_local_version(skill_dir: Path) -> str:
    path = skill_dir / "VERSION"
    if not path.exists():
        raise FileNotFoundError(f"missing VERSION file: {path}")
    return path.read_text(encoding="utf-8").strip()


def fetch_latest_version(url: str, timeout: float) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Installed drawio-diagram-builder skill directory. Defaults to this script's parent skill directory.",
    )
    parser.add_argument(
        "--latest-url",
        default=DEFAULT_VERSION_URL,
        help="URL of the canonical latest VERSION file.",
    )
    parser.add_argument(
        "--latest-version",
        help="Use this latest version instead of fetching from the network. Intended for tests/offline checks.",
    )
    parser.add_argument("--timeout", type=float, default=8.0, help="Network timeout in seconds.")
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    try:
        local = read_local_version(skill_dir)
        local_tuple = parse_version(local)
    except (FileNotFoundError, ValueError) as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        print("reinstall the skill from the canonical repository to recover a versioned copy", file=sys.stderr)
        return 2

    if args.latest_version is not None:
        latest = args.latest_version.strip()
        source = "argument"
    else:
        try:
            latest = fetch_latest_version(args.latest_url, args.timeout)
            source = args.latest_url
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"UNKNOWN: could not fetch latest version: {exc}", file=sys.stderr)
            print(f"local: {local} ({skill_dir})")
            return 2

    try:
        latest_tuple = parse_version(latest)
    except ValueError as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 2

    print(f"local: {local} ({skill_dir})")
    print(f"latest: {latest} ({source})")

    if local_tuple < latest_tuple:
        print("status: OUTDATED")
        print("action: reinstall or update from https://github.com/Will-hxw/drawio-diagram-builder-skill")
        return 1
    if local_tuple > latest_tuple:
        print("status: LOCAL_AHEAD")
        return 0

    print("status: CURRENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
