"""Runtime Secret と .env を同じキーで読む。既にある環境変数を優先する。"""

from __future__ import annotations

import os
from pathlib import Path

# gh がプロセス全体で読む名前は使わない。取得とコメント取得の子プロセスにだけ渡す。
GITHUB_FETCH_TOKEN = "GITHUB_FETCH_TOKEN"
_GH_PROCESS_TOKEN_NAMES = frozenset({"GH_TOKEN", "GITHUB_TOKEN"})


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
        if not name or name in _GH_PROCESS_TOKEN_NAMES:
            continue
        if os.environ.get(name, "").strip():
            continue
        os.environ[name] = value


def gh_env() -> dict[str, str]:
    """取得用トークンだけを、gh 子プロセスの GH_TOKEN として渡す。"""
    env = dict(os.environ)
    token = env.get(GITHUB_FETCH_TOKEN, "").strip()
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    if token:
        env["GH_TOKEN"] = token
    return env
