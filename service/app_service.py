# -*- coding: utf-8 -*-

import json
import time
import uuid
from typing import List, AsyncGenerator, Optional

from openai import AsyncOpenAI
from config.loader import cfg
from utils.log import get_logger

_LLM = cfg.get("llm", {}) or {}

_client = AsyncOpenAI(
    base_url=_LLM.get("base_url"),
    api_key=_LLM.get("api_key"),
    timeout=int(_LLM.get("timeout_seconds")),
)

_DEFAULT_MODEL = _LLM.get("model")


def _body(
    messages: List[dict],
    stream: bool,
    temperature: float,
    max_tokens: Optional[int],
    model: Optional[str],
):
    body = {
        "model": model or _DEFAULT_MODEL,
        "messages": messages,
        "stream": stream,
        "temperature": temperature,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    return body


def _make_full_response(
    model: str,
    content: str,
    _id: Optional[str] = None,
    created: Optional[int] = None,
    finish_reason: Optional[str] = None,
    usage: Optional[dict] = None,
):
    return {
        "id": _id or f"chatcmpl-{uuid.uuid4().hex[:29]}",
        "object": "chat.completion",
        "created": created or int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content or ""},
                "finish_reason": finish_reason or "stop",
            }
        ],
        "usage": usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


async def chat(
    messages: List[dict],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
):
    if not _LLM.get("api_key"):
        raise RuntimeError("llm.api_key 未设置，无法调用上游接口。")

    payload = _body(messages, False, temperature, max_tokens, model)

    resp = await _client.chat.completions.create(**payload)
    data = resp.model_dump()
    oai_id = data.get("id") or f"chatcmpl-{uuid.uuid4().hex[:29]}"

    logger = get_logger()
    if logger:
        await logger.info({"id": oai_id, **payload})
        await logger.info(data)

    return data


async def prepare_stream_chat(
    messages: List[dict],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    if not _LLM.get("api_key"):
        raise RuntimeError("llm.api_key 未设置")

    payload = _body(messages, True, temperature, max_tokens, model)
    logger = get_logger()

    stream = await _client.chat.completions.create(**payload)

    try:
        first_chunk = await stream.__anext__()
    except StopAsyncIteration:
        first_chunk = None
    except Exception:
        raise

    if logger:
        try:
            _id = None
            if first_chunk is not None:
                d0 = first_chunk.model_dump()
                _id = d0.get("id")
            await logger.info({"id": _id, **payload})
        except Exception:
            pass

    async def gen():
        if first_chunk is not None:
            data0 = first_chunk.model_dump()
            yield "data: " + json.dumps(data0, ensure_ascii=False, separators=(",", ":")) + "\n\n"

        try:
            async for chunk in stream:
                data = chunk.model_dump()
                yield "data: " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return gen()
