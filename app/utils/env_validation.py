import os
from typing import Mapping


def require_env(
    keys: list[str],
    *,
    defaults: Mapping[str, str] | None = None,
) -> dict[str, str]:
    defaults = defaults or {}
    values: dict[str, str] = {}
    missing: list[str] = []

    for key in keys:
        val = os.getenv(key)
        if val is None:
            val = defaults.get(key)

        if val is None:
            missing.append(key)
        else:
            values[key] = val

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return values
