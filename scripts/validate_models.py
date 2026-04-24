"""Validate every YAML under models/<provider>/*.yaml against the schema.

Exits 0 if all configs pass, 1 otherwise. Used by CI on every PR.
"""

from __future__ import annotations

import sys

from community_models import ModelSchemaError, iter_model_files, load_model_file


def main() -> int:
    files = list(iter_model_files())
    if not files:
        print("No model configs found under models/. Nothing to validate.")
        return 0

    seen_ids: dict[str, str] = {}
    failures: list[str] = []

    for path in files:
        try:
            data = load_model_file(path)
        except ModelSchemaError as exc:
            failures.append(str(exc))
            continue

        model_id = data["id"]
        if model_id in seen_ids:
            failures.append(
                f"{path}: duplicate model id '{model_id}' (already defined in {seen_ids[model_id]})"
            )
        else:
            seen_ids[model_id] = str(path)

        expected_provider = path.parent.name
        provider_dir_map = {
            "openai": {"openai"},
            "anthropic": {"anthropic"},
            "azure": {"azure"},
            "openrouter": {"openrouter"},
            "google": {"google"},
            "custom": {"custom"},
        }
        allowed = provider_dir_map.get(expected_provider)
        if allowed is not None and data["provider"] not in allowed:
            failures.append(
                f"{path}: provider '{data['provider']}' does not match directory '{expected_provider}/'"
            )

    if failures:
        print(f"\n❌ Validation failed for {len(failures)} config(s):\n")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"✅ Validated {len(files)} model config(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
