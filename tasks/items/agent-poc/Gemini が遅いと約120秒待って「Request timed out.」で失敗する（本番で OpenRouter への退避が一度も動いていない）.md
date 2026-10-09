---
task_id: 68
title: Gemini が遅いと約120秒待って「Request timed out.」で失敗する（本番で OpenRouter への退避が一度も動いていない）
project: agent-poc
status:
  - in_progress
start: ""
end: ""
priority:
  - bug
estimate:
depends_on: []
related: []
github_type:
  - github_issue
github_repo: agent-dev
github_id: Issue#467
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/467
github_updated_at: 2026-10-09T06:29:03Z
backlog_id: MYPL-4238
backlog_url: https://fln2000.backlog.com/view/MYPL-4238
backlog_updated_at: 2026-10-08T12:21:00Z
---
## 概要

本番 2026-10-08 13:36〜13:45 JST、Gemini（gemini-3.8-flash）の応答が遅くなった間に、生成・修正の実行が約 120 秒待ったあと失敗し、利用者の画面に英語の `Request timed out.` が出た。

- agent 側（CloudWatch `/ecs/production-mypl-agentsdk`）: `shop_agent_run_failed error_code=INTERNAL_ERROR` が 8 件、いずれも elapsed 約 120.5 秒。各件 `httpx.ReadTimeout → openai.APITimeoutError: Request timed out.`。ほかに利用者の離脱による `shop_agent_run_cancelled CLIENT_DISCONNECTED`（約 116 秒）が 3 件
- 影響: 6 店舗 8 件のエラー表示。再試行で `GENERATION_ALREADY_RUNNING` / `SESSION_BUSY` が続き、2 セッションは下書きゼロのまま離脱
- 同時刻の gpt-5.6-luna の実行は 5〜11 秒で正常。13:45 以降は平常に戻った
- 約 120 秒の打ち切りは、9/1 以降ではほかに 9/1 の 2 件だけ

期待する挙動は、Gemini が遅いときに利用者を 2 分待たせず、Pro の締切（180 秒）より十分前に OpenRouter へ退避して完了すること。退避できない場合も、日本語で次の一手がわかる文言を出すこと。

## やったこと

origin/main ef17259 で確認した内容。

- LLM クライアントは `httpx.Timeout(connect=10, read=60, write=30, pool=10)`、`max_retries=1`（`agent-poc/src/services/llm_provider.py:46-52`）。Gemini が 60 秒無通信だと、SDK が同じ Gemini に 1 回再試行し、約 121 秒で `APITimeoutError` になる。最初の応答までの専用タイムアウトは無い
- OpenRouter への退避（`sdk_adapter.py` の `_is_fallbackable_agent_error` / ストリームの退避分岐）は、この例外が出たあと、かつ本文やツールの出力がまだ出ていない場合にしか動かない。動いても残りは Pro の締切 180 秒まで約 59 秒
- 本番では退避が一度も動いていない: 13:36〜13:45 に `retrying_before_output` / `fallback` のログは 0 件。9/20〜10/8 に広げても `fallback_attempted:true` は 0 件。`AGENT_FALLBACK_PROVIDER` / `OPENROUTER_AGENT_MODEL` が本番で未設定とみられる（設定値そのものは未確認）
- 例外は generic except で `INTERNAL_ERROR` + `str(exc)` になり、英語のまま画面に出る（#166 / #466 と同じ経路）

## 残りのやること

- 本番の退避設定（`AGENT_FALLBACK_PROVIDER=openrouter`、`OPENROUTER_API_KEY`、`OPENROUTER_AGENT_MODEL`）を確認する。無効が意図的なら理由を Issue に残す
- 最初の応答（最初のイベント）までのタイムアウトを短く設ける（目安 20〜30 秒）
- 退避が有効なとき、同じ Gemini への SDK 自動再試行（`max_retries`）で時間を使わず、すぐ退避する
- Pro の締切 180 秒から逆算した全体の時間予算を持ち、Gemini 側と退避先の持ち時間を分ける
- タイムアウト時の利用者向け文言を日本語の固定文言にする（#166 と調整）
- 遅い provider を模した fake で、退避が締切内に完了する回帰テストを追加する
