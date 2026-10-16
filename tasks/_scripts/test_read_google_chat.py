"""read_google_chat.py の単体テスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from read_google_chat import (
    GoogleChatApiClient,
    ParseError,
    parse_message_reference,
    read_context,
    save_token,
    THREAD_LIMIT,
)


class FakeChatClient:
    def __init__(
        self,
        messages: dict[str, dict],
        space: dict,
        thread_order: list[str],
        space_timeline: list[str],
    ) -> None:
        self._messages = messages
        self._space = space
        self._thread_order = thread_order
        self._space_timeline = space_timeline

    def get_message(self, name: str) -> dict:
        return self._messages[name]

    def get_space(self, name: str) -> dict:
        return self._space

    def list_thread_messages(
        self, space_name: str, thread_name: str, limit: int
    ) -> tuple[list[dict], bool]:
        collected = []
        truncated = False
        for message_name in self._thread_order:
            if len(collected) >= limit:
                truncated = True
                break
            collected.append(self._messages[message_name])
        return collected, truncated

    def neighbor_before(self, space_name: str, create_time: str) -> dict | None:
        before_name = None
        for message_name in self._space_timeline:
            msg = self._messages[message_name]
            if msg["createTime"] < create_time:
                before_name = message_name
        return self._messages[before_name] if before_name else None

    def neighbor_after(self, space_name: str, create_time: str) -> dict | None:
        for message_name in self._space_timeline:
            msg = self._messages[message_name]
            if msg["createTime"] > create_time:
                return msg
        return None


def _msg(
    name: str,
    create_time: str,
    thread_name: str,
    text: str,
    *,
    space_id: str = "SPACE",
    thread_id: str = "THREAD",
) -> dict:
    message_id = name.split("/messages/", 1)[1]
    return {
        "name": name,
        "createTime": create_time,
        "text": text,
        "thread": {"name": thread_name},
        "sender": {"displayName": f"user-{message_id}"},
    }


class ParseMessageReferenceTests(unittest.TestCase):
    def test_room_url(self) -> None:
        ref = parse_message_reference(
            "https://chat.google.com/room/AAA/BBB/CCC.MMM"
        )
        self.assertEqual(ref.message_name, "spaces/AAA/messages/CCC.MMM")
        self.assertEqual(ref.space_id, "AAA")
        self.assertEqual(ref.thread_id, "BBB")

    def test_dm_url(self) -> None:
        ref = parse_message_reference("https://chat.google.com/dm/X/Y/Z")
        self.assertEqual(ref.message_name, "spaces/X/messages/Z")

    def test_resource_name(self) -> None:
        ref = parse_message_reference("spaces/AAA/messages/BBB.CCC")
        self.assertEqual(ref.message_name, "spaces/AAA/messages/BBB.CCC")

    def test_rejects_space_url(self) -> None:
        with self.assertRaises(ParseError):
            parse_message_reference("https://chat.google.com/room/AAA")

    def test_rejects_thread_url(self) -> None:
        with self.assertRaises(ParseError):
            parse_message_reference("https://chat.google.com/room/AAA/BBB")

    def test_rejects_unknown(self) -> None:
        with self.assertRaises(ParseError):
            parse_message_reference("https://example.com/")


class ReadContextTests(unittest.TestCase):
    def _client(self) -> FakeChatClient:
        thread = "spaces/SPACE/threads/THREAD"
        m1 = _msg(
            "spaces/SPACE/messages/m1",
            "2026-01-01T10:00:00Z",
            thread,
            "thread-1",
        )
        m2 = _msg(
            "spaces/SPACE/messages/m2",
            "2026-01-01T10:05:00Z",
            thread,
            "target",
        )
        m3 = _msg(
            "spaces/SPACE/messages/m3",
            "2026-01-01T10:10:00Z",
            thread,
            "thread-3",
        )
        other_thread = "spaces/SPACE/threads/OTHER"
        before_other = _msg(
            "spaces/SPACE/messages/before",
            "2026-01-01T09:55:00Z",
            other_thread,
            "before-other-thread",
        )
        after_other = _msg(
            "spaces/SPACE/messages/after",
            "2026-01-01T10:15:00Z",
            other_thread,
            "after-other-thread",
        )
        messages = {
            m1["name"]: m1,
            m2["name"]: m2,
            m3["name"]: m3,
            before_other["name"]: before_other,
            after_other["name"]: after_other,
        }
        timeline = [
            before_other["name"],
            m1["name"],
            m2["name"],
            m3["name"],
            after_other["name"],
        ]
        return FakeChatClient(
            messages=messages,
            space={
                "name": "spaces/SPACE",
                "displayName": "Test Space",
                "spaceType": "SPACE",
            },
            thread_order=[m1["name"], m2["name"], m3["name"]],
            space_timeline=timeline,
        )

    def test_thread_sorted_and_neighbors(self) -> None:
        url = "https://chat.google.com/room/SPACE/THREAD/m2"
        payload = read_context(url, self._client())
        times = [item["createTime"] for item in payload["thread"]]
        self.assertEqual(times, sorted(times))
        self.assertEqual(payload["target"]["text"], "target")
        self.assertIsNotNone(payload["before"])
        self.assertTrue(payload["before"]["inThread"])
        self.assertEqual(payload["before"]["message"]["text"], "thread-1")
        self.assertIsNotNone(payload["after"])
        self.assertTrue(payload["after"]["inThread"])
        self.assertEqual(payload["after"]["message"]["text"], "thread-3")

    def test_truncated_thread(self) -> None:
        thread = "spaces/SPACE/threads/T"
        messages = {}
        order = []
        base = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        for index in range(THREAD_LIMIT + 5):
            name = f"spaces/SPACE/messages/m{index}"
            create_time = (base + timedelta(minutes=index)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            msg = _msg(
                name,
                create_time,
                thread,
                f"text-{index}",
                thread_id="T",
            )
            messages[name] = msg
            order.append(name)
        target = messages[order[THREAD_LIMIT // 2]]
        client = FakeChatClient(
            messages=messages,
            space={"name": "spaces/SPACE", "displayName": "Big", "spaceType": "SPACE"},
            thread_order=order,
            space_timeline=order,
        )
        payload = read_context(
            f"spaces/SPACE/messages/{target['name'].split('/')[-1]}",
            client,
        )
        self.assertTrue(payload["truncated"])
        self.assertEqual(len(payload["thread"]), THREAD_LIMIT)


class TokenAndGitignoreTests(unittest.TestCase):
    def test_save_token_writes_only_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".google-chat-token.json"
            save_token(path, json.dumps({"token": "secret"}))
            self.assertTrue(path.is_file())
            self.assertNotIn("message", path.read_text(encoding="utf-8"))

    def test_gitignore_lists_token_file(self) -> None:
        text = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn(".google-chat-token.json", text)


class GoogleChatApiClientErrorTests(unittest.TestCase):
    def test_maps_403(self) -> None:
        from unittest.mock import Mock

        from googleapiclient.errors import HttpError

        resp = Mock()
        resp.status = 403
        error = HttpError(resp, b"forbidden")

        def boom() -> dict:
            raise error

        with self.assertRaises(RuntimeError) as ctx:
            GoogleChatApiClient._call(boom)
        self.assertIn("403", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
