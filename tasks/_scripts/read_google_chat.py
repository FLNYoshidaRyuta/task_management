"""Google Chat の指定メッセージ URL から会話を読み、標準出力へ JSON を出す。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from runtime_env import load_env_file

TOKEN_FILENAME = ".google-chat-token.json"
THREAD_LIMIT = 500
SCOPES = (
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.spaces.readonly",
)

BROWSER_URL_RE = re.compile(
    r"^https://chat\.google\.com/(?P<kind>room|dm)/"
    r"(?P<space>[^/]+)/(?P<thread>[^/]+)/(?P<message>[^/]+)/?$"
)
RESOURCE_NAME_RE = re.compile(r"^spaces/(?P<space>[^/]+)/messages/(?P<message>.+)$")
SPACE_ONLY_RE = re.compile(
    r"^https://chat\.google\.com/(?:room|dm)/[^/]+/?$"
)
THREAD_ONLY_RE = re.compile(
    r"^https://chat\.google\.com/(?:room|dm)/[^/]+/[^/]+/?$"
)


class ChatClient(Protocol):
    def get_message(self, name: str) -> dict[str, Any]: ...

    def get_space(self, name: str) -> dict[str, Any]: ...

    def list_thread_messages(
        self, space_name: str, thread_name: str, limit: int
    ) -> tuple[list[dict[str, Any]], bool]: ...

    def neighbor_before(
        self, space_name: str, create_time: str
    ) -> dict[str, Any] | None: ...

    def neighbor_after(
        self, space_name: str, create_time: str
    ) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class ParsedMessageRef:
    message_name: str
    space_id: str
    thread_id: str | None
    browser_url: str | None


class ParseError(ValueError):
    pass


def parse_message_reference(url_or_name: str) -> ParsedMessageRef:
    text = url_or_name.strip()
    if not text:
        raise ParseError("URL またはメッセージ名が空です。")

    if SPACE_ONLY_RE.fullmatch(text) or THREAD_ONLY_RE.fullmatch(text):
        raise ParseError(
            "メッセージ URL が必要です。スペース URL やスレッド URL だけでは読めません。"
        )

    matched = BROWSER_URL_RE.fullmatch(text)
    if matched:
        space_id = matched.group("space")
        thread_id = matched.group("thread")
        message_id = matched.group("message")
        return ParsedMessageRef(
            message_name=f"spaces/{space_id}/messages/{message_id}",
            space_id=space_id,
            thread_id=thread_id,
            browser_url=text,
        )

    matched = RESOURCE_NAME_RE.fullmatch(text)
    if matched:
        return ParsedMessageRef(
            message_name=text,
            space_id=matched.group("space"),
            thread_id=None,
            browser_url=None,
        )

    raise ParseError(f"未対応の URL またはメッセージ名です: {text}")


def parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _space_id_from_name(space_name: str) -> str:
    prefix = "spaces/"
    if not space_name.startswith(prefix):
        return space_name
    return space_name[len(prefix) :]


def _thread_id_from_name(thread_name: str) -> str | None:
    marker = "/threads/"
    if marker not in thread_name:
        return None
    return thread_name.split(marker, 1)[1]


def _message_id_from_name(message_name: str) -> str:
    marker = "/messages/"
    if marker not in message_name:
        return message_name
    return message_name.split(marker, 1)[1]


def browser_url_for_message(
    space_type: str, space_id: str, thread_id: str, message_id: str
) -> str:
    kind = "dm" if space_type == "DIRECT_MESSAGE" else "room"
    return f"https://chat.google.com/{kind}/{space_id}/{thread_id}/{message_id}"


def message_text(raw: dict[str, Any]) -> str:
    text = (raw.get("text") or "").strip()
    if text:
        return text
    return (raw.get("argumentText") or "").strip()


def attachment_names(raw: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in raw.get("attachment") or []:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or item.get("contentName") or "").strip()
        if name:
            names.append(name)
    return names


def sender_label(raw: dict[str, Any]) -> str:
    sender = raw.get("sender") or {}
    if not isinstance(sender, dict):
        return ""
    display = (sender.get("displayName") or "").strip()
    if display:
        return display
    return (sender.get("name") or "").strip()


def normalize_message(
    raw: dict[str, Any],
    *,
    space_type: str,
    url_hint: str | None,
) -> dict[str, Any]:
    name = (raw.get("name") or "").strip()
    space_id = _space_id_from_name(name.split("/messages/")[0]) if name else ""
    thread_name = (raw.get("thread") or {}).get("name") or ""
    thread_id = _thread_id_from_name(thread_name) or ""
    message_id = _message_id_from_name(name)
    url = url_hint
    if not url and space_id and thread_id and message_id:
        url = browser_url_for_message(space_type, space_id, thread_id, message_id)
    return {
        "name": name,
        "createTime": raw.get("createTime") or "",
        "sender": sender_label(raw),
        "text": message_text(raw),
        "attachments": attachment_names(raw),
        "url": url or "",
        "threadName": thread_name,
    }


def wrap_neighbor(
    raw: dict[str, Any] | None,
    *,
    space_type: str,
    target_thread_name: str,
) -> dict[str, Any] | None:
    if raw is None:
        return None
    normalized = normalize_message(raw, space_type=space_type, url_hint=None)
    thread_name = normalized.get("threadName") or ""
    return {
        "message": normalized,
        "inThread": bool(thread_name and thread_name == target_thread_name),
    }


def read_context(url_or_name: str, client: ChatClient) -> dict[str, Any]:
    ref = parse_message_reference(url_or_name)
    target_raw = client.get_message(ref.message_name)
    space_name = f"spaces/{ref.space_id}"
    space_raw = client.get_space(space_name)
    space_type = (space_raw.get("spaceType") or "SPACE").strip()
    target = normalize_message(
        target_raw,
        space_type=space_type,
        url_hint=ref.browser_url,
    )
    thread_name = (target_raw.get("thread") or {}).get("name") or ""
    if not thread_name:
        raise RuntimeError("指定メッセージにスレッド情報がありません。")

    thread_raw, truncated = client.list_thread_messages(
        space_name, thread_name, THREAD_LIMIT
    )
    thread = [
        normalize_message(item, space_type=space_type, url_hint=None)
        for item in thread_raw
    ]
    thread.sort(key=lambda item: parse_time(item["createTime"]))

    create_time = target["createTime"]
    before = wrap_neighbor(
        client.neighbor_before(space_name, create_time),
        space_type=space_type,
        target_thread_name=thread_name,
    )
    after = wrap_neighbor(
        client.neighbor_after(space_name, create_time),
        space_type=space_type,
        target_thread_name=thread_name,
    )

    return {
        "space": {
            "name": space_raw.get("name") or space_name,
            "displayName": (space_raw.get("displayName") or "").strip(),
            "spaceType": space_type,
        },
        "target": target,
        "thread": thread,
        "before": before,
        "after": after,
        "truncated": truncated,
    }


class GoogleChatApiClient:
    """google-api-python-client による Chat API 実装。"""

    def __init__(self, service: Any) -> None:
        self._service = service

    def get_message(self, name: str) -> dict[str, Any]:
        return self._call(
            lambda: self._service.spaces().messages().get(name=name).execute()
        )

    def get_space(self, name: str) -> dict[str, Any]:
        return self._call(lambda: self._service.spaces().get(name=name).execute())

    def list_thread_messages(
        self, space_name: str, thread_name: str, limit: int
    ) -> tuple[list[dict[str, Any]], bool]:
        escaped = thread_name.replace('"', '\\"')
        filter_text = f'thread.name = "{escaped}"'
        collected: list[dict[str, Any]] = []
        page_token: str | None = None
        truncated = False
        while True:
            request = (
                self._service.spaces()
                .messages()
                .list(
                    parent=space_name,
                    filter=filter_text,
                    orderBy="createTime asc",
                    pageSize=min(100, limit - len(collected)),
                    pageToken=page_token,
                )
            )
            response = self._call(request.execute)
            messages = response.get("messages") or []
            for item in messages:
                if len(collected) >= limit:
                    truncated = True
                    break
                collected.append(item)
            if truncated:
                break
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return collected, truncated

    def neighbor_before(
        self, space_name: str, create_time: str
    ) -> dict[str, Any] | None:
        filter_text = f'createTime < "{create_time}"'
        response = self._call(
            lambda: self._service.spaces()
            .messages()
            .list(
                parent=space_name,
                filter=filter_text,
                orderBy="createTime desc",
                pageSize=1,
            )
            .execute()
        )
        messages = response.get("messages") or []
        return messages[0] if messages else None

    def neighbor_after(
        self, space_name: str, create_time: str
    ) -> dict[str, Any] | None:
        filter_text = f'createTime > "{create_time}"'
        response = self._call(
            lambda: self._service.spaces()
            .messages()
            .list(
                parent=space_name,
                filter=filter_text,
                orderBy="createTime asc",
                pageSize=1,
            )
            .execute()
        )
        messages = response.get("messages") or []
        return messages[0] if messages else None

    @staticmethod
    def _call(action: Any) -> dict[str, Any]:
        try:
            from googleapiclient.errors import HttpError
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("google-api-python-client is required") from exc
        try:
            result = action()
        except HttpError as exc:
            if exc.resp is not None and exc.resp.status == 403:
                raise RuntimeError(
                    "Google Chat API が 403 を返しました。"
                    "同意したユーザーがスペースのメンバーでない、"
                    "または Workspace 管理者が API を許可していない可能性があります。"
                ) from exc
            raise RuntimeError(f"Google Chat API の呼び出しに失敗しました: {exc}") from exc
        if not isinstance(result, dict):
            raise RuntimeError("Google Chat API の応答が不正です。")
        return result


def load_credentials(vault: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "google-auth, google-auth-oauthlib が必要です。requirements.txt をインストールしてください。"
        ) from exc

    load_env_file(vault / ".env")
    client_id = os.environ.get("GOOGLE_CHAT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CHAT_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError(
            "GOOGLE_CHAT_CLIENT_ID と GOOGLE_CHAT_CLIENT_SECRET が必要です。"
        )

    token_path = vault / TOKEN_FILENAME
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        save_token(token_path, creds.to_json())

    return creds


def save_token(path: Path, token_json: str) -> None:
    """認証トークンだけを書く。メッセージ本文は書かない。"""
    path.write_text(token_json, encoding="utf-8")


def build_api_client(vault: Path) -> GoogleChatApiClient:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("google-api-python-client is required") from exc
    creds = load_credentials(vault)
    service = build("chat", "v1", credentials=creds, cache_discovery=False)
    return GoogleChatApiClient(service)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read Google Chat message context.")
    parser.add_argument("--url", required=True, help="Message URL or resource name")
    parser.add_argument(
        "--vault",
        default=".",
        help="Vault root (default: current directory)",
    )
    args = parser.parse_args(argv)

    vault = Path(args.vault).resolve()
    try:
        client = build_api_client(vault)
        payload = read_context(args.url, client)
    except ParseError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
