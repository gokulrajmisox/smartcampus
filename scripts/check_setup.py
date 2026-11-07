#!/usr/bin/env python3
"""Pre-flight check for the CampusAI demo / local setup.

Run before presenting or after a fresh clone:

    python3 scripts/check_setup.py
    uv run python scripts/check_setup.py

It verifies, without starting Streamlit and without any network access:

  * Python >= 3.11 (the README prerequisite)
  * the packages the app imports are installed
  * uv.lock is in sync with pyproject.toml (only when `uv` is on PATH)
  * the OSM campus graph exists and parses as XML
  * campus_data/demo_locations.json exists, parses, and lists usable POIs
  * campus_data/roles.json exists and parses
  * the optional assets (.streamlit/config.toml, assets/style.css) exist
  * a Gemini key is configured (warning only -- local routing works without it)
  * TCP port 8501 is free (warning only)

Why this exists: CampusPathfinder loads demo_locations.json from a
CWD-relative path and, on ANY error, silently falls back to just two
POIs (Main Gate, Library) -- routes to every other place then fail or
report 0.0 m, which is exactly the kind of thing you discover mid-demo.
This script fails loudly instead, before Streamlit starts.

Exit code is 0 only when no check failed. Warnings never fail the run.
No secrets are printed: key values are never read, only their presence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MIN_PYTHON = (3, 11)
REQUIRED_PACKAGES = [
    # (import name, pip name) -- kept in sync with pyproject.toml
    ("streamlit", "streamlit"),
    ("streamlit_folium", "streamlit-folium"),
    ("osmnx", "osmnx"),
    ("networkx", "networkx"),
    ("folium", "folium"),
    ("google.genai", "google-genai"),
    ("dotenv", "python-dotenv"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("pytest", "pytest"),
]
REQUIRED_FILES = [
    "app.py",
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
]
OSM_PATH = "attached_assets/sathyabama_small.osm"
POI_PATH = "campus_data/demo_locations.json"
ROLES_PATH = "campus_data/roles.json"
STREAMLIT_PORT = 8501


class Results:
    """Collects one line per check; exit code follows the failure count."""

    def __init__(self) -> None:
        self.passed = 0
        self.warned = 0
        self.failed = 0

    def ok(self, name: str, detail: str) -> None:
        self.passed += 1
        print(f"[PASS] {name} -- {detail}")

    def warn(self, name: str, detail: str) -> None:
        self.warned += 1
        print(f"[WARN] {name} -- {detail}")

    def fail(self, name: str, detail: str, fix: str = "") -> None:
        self.failed += 1
        line = f"[FAIL] {name} -- {detail}"
        if fix:
            line += f" (fix: {fix})"
        print(line)

    def summary(self) -> bool:
        print(
            f"\n{self.passed} passed, {self.warned} warnings, "
            f"{self.failed} failed."
        )
        if self.failed:
            print("Setup is NOT ready -- fix the [FAIL] items above and re-run.")
            return False
        if self.warned:
            print("Setup is ready; review the [WARN] items above.")
        else:
            print("Setup is ready.")
        return True


def default_root() -> Path:
    # scripts/check_setup.py -> repo root, whatever the working directory is.
    return Path(__file__).resolve().parent.parent


def check_python(results: Results) -> None:
    if sys.version_info >= MIN_PYTHON:
        results.ok(
            "python",
            f"Python {sys.version.split()[0]} (>= "
            f"{'.'.join(map(str, MIN_PYTHON))} required)",
        )
    else:
        results.fail(
            "python",
            f"Python {sys.version.split()[0]} is too old "
            f"(need >= {'.'.join(map(str, MIN_PYTHON))})",
            "install Python 3.11 or newer",
        )


def check_root_files(root: Path, results: Results) -> None:
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if not missing:
        results.ok("repo-root", f"ran from {root} (app.py, manifests present)")
    else:
        results.fail(
            "repo-root",
            f"missing at {root}: {', '.join(missing)}",
            "run from a fresh clone of the smartcampus repo",
        )


def _is_importable(import_name: str) -> bool:
    # find_spec raises (rather than returning None) when a parent
    # package of a dotted name is missing entirely, e.g. "google.genai"
    # with no `google` package installed.
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, ValueError):
        return False


def check_dependencies(results: Results) -> None:
    missing = [
        pip_name
        for import_name, pip_name in REQUIRED_PACKAGES
        if not _is_importable(import_name)
    ]
    if not missing:
        results.ok(
            "dependencies",
            f"all {len(REQUIRED_PACKAGES)} required packages importable",
        )
    else:
        results.fail(
            "dependencies",
            f"not installed: {', '.join(missing)}",
            "uv sync --frozen",
        )


def check_uv_lock(root: Path, results: Results) -> None:
    uv = shutil.which("uv")
    if uv is None:
        results.warn(
            "uv-lock",
            "uv not on PATH, lock check skipped "
            "(install uv: https://docs.astral.sh/uv/)",
        )
        return
    try:
        proc = subprocess.run(
            [uv, "lock", "--check"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        results.warn("uv-lock", f"could not run `uv lock --check`: {exc}")
        return
    if proc.returncode == 0:
        results.ok("uv-lock", "uv.lock is in sync with pyproject.toml")
    else:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        results.fail(
            "uv-lock",
            f"uv.lock out of sync: {detail[0] if detail else 'see uv output'}",
            "uv lock",
        )


def check_osm_graph(root: Path, results: Results) -> None:
    path = root / OSM_PATH
    if not path.is_file():
        results.fail(
            "osm-graph",
            f"{OSM_PATH} missing",
            "restore it from the repo (git checkout -- attached_assets/)",
        )
        return
    if path.stat().st_size == 0:
        results.fail("osm-graph", f"{OSM_PATH} is empty", "re-download the OSM file")
        return
    nodes = ways = 0
    try:
        for _event, element in ET.iterparse(path, events=("end",)):
            if element.tag == "node":
                nodes += 1
            elif element.tag == "way":
                ways += 1
            element.clear()
    except ET.ParseError as exc:
        results.fail(
            "osm-graph",
            f"{OSM_PATH} is not valid XML ({exc})",
            "re-download the OSM file",
        )
        return
    if nodes == 0 or ways == 0:
        results.fail(
            "osm-graph",
            f"{OSM_PATH} parses but has {nodes} nodes / {ways} ways",
            "re-download the OSM file",
        )
        return
    results.ok("osm-graph", f"{OSM_PATH}: {nodes} nodes, {ways} ways")


def check_poi_data(root: Path, results: Results) -> None:
    path = root / POI_PATH
    if not path.is_file():
        # This is the silent-fallback trap: without this file the app
        # starts fine but only knows Main Gate + Library.
        results.fail(
            "poi-data",
            f"{POI_PATH} missing -- the app would silently fall back "
            "to 2 POIs (Main Gate, Library) and other routes would fail",
            "restore it from the repo (git checkout -- campus_data/)",
        )
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        results.fail(
            "poi-data",
            f"{POI_PATH} unreadable ({exc}) -- the app would silently "
            "fall back to 2 POIs",
            "restore it from the repo (git checkout -- campus_data/)",
        )
        return
    locations = data.get("locations") if isinstance(data, dict) else None
    if not isinstance(locations, list) or not locations:
        results.fail(
            "poi-data",
            f"{POI_PATH} has no usable 'locations' list",
            "restore it from the repo (git checkout -- campus_data/)",
        )
        return
    problems = []
    names = set()
    for entry in locations:
        name = entry.get("name") if isinstance(entry, dict) else None
        coords = entry.get("coordinates") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not name:
            problems.append("entry without a name")
            continue
        if name in names:
            problems.append(f"duplicate name {name!r}")
        names.add(name)
        if not isinstance(coords, dict):
            problems.append(f"{name}: no coordinates")
            continue
        lat, lng = coords.get("lat"), coords.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            problems.append(f"{name}: coordinates are not numbers")
    if problems:
        results.fail("poi-data", "; ".join(sorted(set(problems)))[:300], "fix " + POI_PATH)
        return
    detail = f"{len(locations)} POIs with coordinates"
    if len(locations) < 3:
        results.warn(
            "poi-data",
            f"{detail} -- thin demo set (the app falls back to 2 POIs "
            "if this file fails to load)",
        )
    else:
        results.ok("poi-data", detail)


def check_roles_data(root: Path, results: Results) -> None:
    path = root / ROLES_PATH
    if not path.is_file():
        results.fail(
            "roles-data",
            f"{ROLES_PATH} missing",
            "restore it from the repo (git checkout -- campus_data/)",
        )
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        results.fail("roles-data", f"{ROLES_PATH} unreadable ({exc})", "fix " + ROLES_PATH)
        return
    roles = data.get("roles") if isinstance(data, dict) else None
    if isinstance(roles, dict) and roles:
        results.ok(
            "roles-data",
            f"{len(roles)} roles defined ({', '.join(sorted(roles))})",
        )
    elif isinstance(roles, list) and roles:
        results.ok("roles-data", f"{len(roles)} roles defined")
    else:
        results.fail(
            "roles-data",
            f"{ROLES_PATH} has no usable 'roles' mapping/list",
            "fix " + ROLES_PATH,
        )


def check_optional_assets(root: Path, results: Results) -> None:
    for relpath, note in (
        (".streamlit/config.toml", "Streamlit theme (defaults used if missing)"),
        ("assets/style.css", "custom CSS (app runs without it)"),
    ):
        if (root / relpath).is_file():
            results.ok("optional-assets", f"{relpath} present")
        else:
            results.warn("optional-assets", f"{relpath} missing -- {note}")


def _env_file_has_key(root: Path) -> bool:
    env_file = root / ".env"
    if not env_file.is_file():
        return False
    try:
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY=") and "your-gemini-api-key" not in line:
                return True
    except OSError:
        return False
    return False


def check_env(root: Path, results: Results) -> None:
    # Presence only -- the value is never read or printed.
    if os.environ.get("GEMINI_API_KEY") or _env_file_has_key(root):
        results.ok("env", "GEMINI_API_KEY configured (Gemini answers enabled)")
    else:
        results.warn(
            "env",
            "GEMINI_API_KEY not set -- Gemini answers disabled, "
            "local routing still works (copy .env.example to .env to enable)",
        )


def check_port(results: Results) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", STREAMLIT_PORT))
    except OSError:
        results.warn(
            "port",
            f"port {STREAMLIT_PORT} is already in use -- Streamlit may "
            "fail to start or pick another port",
        )
    else:
        results.ok("port", f"port {STREAMLIT_PORT} is free")
    finally:
        sock.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-flight check for the CampusAI demo / local setup."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repo root to check (default: parent of the scripts/ directory)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else default_root()

    print(f"CampusAI setup check -- repo root: {root}")
    results = Results()
    check_python(results)
    check_root_files(root, results)
    check_dependencies(results)
    check_uv_lock(root, results)
    check_osm_graph(root, results)
    check_poi_data(root, results)
    check_roles_data(root, results)
    check_optional_assets(root, results)
    check_env(root, results)
    check_port(results)
    return 0 if results.summary() else 1


if __name__ == "__main__":
    raise SystemExit(main())
