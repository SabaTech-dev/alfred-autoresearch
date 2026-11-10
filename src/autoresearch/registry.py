"""Optional experiment registry (S3).

Records known experiment directories so `autoresearch experiments` can list
them. The cwd-only mode keeps working when the registry is absent or
unwritable: registration failures are silently ignored.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_VERSION = 1


def registry_home() -> Path:
    """Root of the registry; override with AUTORESEARCH_HOME."""
    env = os.environ.get("AUTORESEARCH_HOME")
    if env:
        return Path(env)
    return Path.home() / ".autoresearch"


def registry_path() -> Path:
    return registry_home() / "registry.json"


def register(cwd: Path, name: str | None, metric_name: str) -> None:
    """Upsert an experiment entry keyed by its working directory.

    Best-effort: any failure (unwritable home, corrupt file) is swallowed so
    the engine never breaks because of the optional registry.
    """
    try:
        data = _load()
        data["experiments"][str(cwd)] = {
            "name": name,
            "metric_name": metric_name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path = registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except OSError:
        pass


def list_experiments() -> list[dict]:
    """Return known experiments sorted by most recent update."""
    entries = [{"cwd": cwd, **info} for cwd, info in _load()["experiments"].items()]
    entries.sort(key=lambda e: e.get("updated_at", ""), reverse=True)
    return entries


def _load() -> dict:
    path = registry_path()
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict) and isinstance(data.get("experiments"), dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"version": REGISTRY_VERSION, "experiments": {}}
