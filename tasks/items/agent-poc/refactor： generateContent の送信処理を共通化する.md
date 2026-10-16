---
task_id: 35
title: refactor： generateContent の送信処理を共通化する
project: agent-poc
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: agent-dev
github_id: Issue#461
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/461
github_updated_at: 2026-09-30 12:40:04+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

Gemini の `generateContent` 送信が、同じ形のまま3箇所に分かれています。

## やったこと

- `agent-poc/src/services/news_image_ai.py` の `_call_gemini_json()`
- `agent-poc/src/services/material_vision_analyzer.py` の `_analyze_material_ref_gemini()`
- `agent-poc/src/services/gemini_web_search.py` の `fetch_gemini_web_search()`

## 残りのやること

- `agent-poc/src/services/news_image_ai.py` の `_call_gemini_json()`
- `agent-poc/src/services/material_vision_analyzer.py` の `_analyze_material_ref_gemini()`
- `agent-poc/src/services/gemini_web_search.py` の `fetch_gemini_web_search()`
