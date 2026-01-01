from __future__ import annotations

import json
import time
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

_state = {"calls": 0}


@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body: Dict[str, Any] = await req.json()
    _state["calls"] += 1

    model = body.get("model", "fake-model")

    # First call: invalid output
    if _state["calls"] == 1:
        assistant_content = "yaml:\n  this_is: not_json"
    else:
        assistant_content = json.dumps(
            {
                "rule": {
                    # "name": "regex.cc.test", # force missing name for testing
                    "domain": "Financial",
                    "description": "Test credit card regex",
                    "data_category": "Credit Card Number",
                    "pattern": r"\b4012(?:[ -]?8888){2}[ -]?1881\b",
                }
            }
        )

    resp = {
        "id": f"chatcmpl-fake-{_state['calls']}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls": [],
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "stats": {},
        "system_fingerprint": "fake-lmstudio",
    }

    print(f"[fake-lmstudio] call #{_state['calls']}")
    return JSONResponse(resp)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_fake_lm_studio:app",
        host="127.0.0.1",
        port=1234,
        log_level="info",
        reload=False,
    )
