"""Runtime Secret と .env を同じキーで読む。既にある環境変数を優先する。"""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(env_path: Path) -> None:
    """未設定のキーだけ .env から入れる。空の値は未設定として扱う。"""
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if "=" not in text:
            continue
        name, value = text.split("=", 1)
        name = name.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if not name:
            continue
        if os.environ.get(name, "").strip():
            continue
        os.environ[name] = value


def gh_env() -> dict[str, str]:
    """gh に渡す環境。GH_TOKEN があるときだけ gh がそれを使う。"""
    env = dict(os.environ)
    token = env.get("GH_TOKEN", "").strip()
    if token:
        env["GH_TOKEN"] = token
    else:
        env.pop("GH_TOKEN", None)
    return env
