"""Loader for community-contributed model YAMLs under models/<provider>/*.yaml.

Each YAML is validated against the schema defined in models/SCHEMA.md. Validated
entries are merged with the built-in hardcoded registry so contributors can add
new models via PR without editing Python.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required to load community model configs. "
        "Install it with `pip install pyyaml` or reinstall requirements.txt."
    ) from exc


MODELS_ROOT = Path(__file__).resolve().parent.parent / "models"

VALID_PROVIDERS = {"openai", "anthropic", "azure", "openrouter", "google", "custom"}
VALID_ROUTES = {
    "openrouter_chat",
    "azure_openai_chat",
    "azure_ai_inference",
    "azure_openai_responses",
    "openai_chat",
    "anthropic_messages",
    "custom_http",
}
REQUIRED_FIELDS = ("id", "display_name", "provider", "route", "submitted_by", "submission_date")


class ModelSchemaError(ValueError):
    """Raised when a community model YAML fails validation."""


def _validate(path: Path, data: Dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise ModelSchemaError(f"{path}: missing required fields: {', '.join(missing)}")

    if data["provider"] not in VALID_PROVIDERS:
        raise ModelSchemaError(
            f"{path}: provider '{data['provider']}' is not in {sorted(VALID_PROVIDERS)}"
        )
    if data["route"] not in VALID_ROUTES:
        raise ModelSchemaError(
            f"{path}: route '{data['route']}' is not in {sorted(VALID_ROUTES)}"
        )

    if data["provider"] == "openrouter":
        pricing = data.get("pricing") or {}
        for key in ("prompt", "completion"):
            if pricing.get(key) is None:
                raise ModelSchemaError(
                    f"{path}: openrouter models must declare pricing.{key} (USD/token)."
                )

    submitted_by = str(data["submitted_by"])
    if not submitted_by.startswith("@"):
        raise ModelSchemaError(
            f"{path}: submitted_by must start with '@' (GitHub handle)."
        )


def iter_model_files(root: Optional[Path] = None) -> Iterable[Path]:
    root = root or MODELS_ROOT
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def load_model_file(path: Path) -> Dict[str, Any]:
    with path.open("r") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ModelSchemaError(f"{path}: top-level YAML must be a mapping.")
    _validate(path, data)
    data.setdefault("pricing", {"prompt": 0.0, "completion": 0.0})
    data.setdefault("premium", False)
    data.setdefault("tags", [])
    data["_source_path"] = str(path.relative_to(path.parent.parent.parent))
    return data


def load_all(root: Optional[Path] = None) -> List[Dict[str, Any]]:
    models: List[Dict[str, Any]] = []
    seen_ids: Dict[str, Path] = {}
    for path in iter_model_files(root):
        data = load_model_file(path)
        model_id = data["id"]
        if model_id in seen_ids:
            raise ModelSchemaError(
                f"Duplicate model id '{model_id}' in {path} and {seen_ids[model_id]}."
            )
        seen_ids[model_id] = path
        models.append(data)
    return models


def registry_entries(include_premium: bool = False) -> List[Dict[str, Any]]:
    """Return community models shaped like the entries in model_registry.DEFAULT_MODELS."""
    entries: List[Dict[str, Any]] = []
    for model in load_all():
        if model.get("premium") and not include_premium:
            continue
        entries.append(
            {
                "name": model["id"],
                "route": model["route"],
                "provider": model["provider"],
                "display_name": model["display_name"],
                "pricing": model.get("pricing", {}),
                "notes": model.get("notes", ""),
                "tags": model.get("tags", []),
                "submitted_by": model.get("submitted_by"),
                "submission_date": model.get("submission_date"),
                "homepage": model.get("homepage"),
                "license": model.get("license"),
                "_source_path": model.get("_source_path"),
            }
        )
    return entries


if __name__ == "__main__":
    import json

    entries = registry_entries(include_premium=True)
    print(json.dumps(entries, indent=2, default=str))
    print(f"\nLoaded {len(entries)} community model configs.")
