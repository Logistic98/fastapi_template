# -*- coding: utf-8 -*-

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

from utils.request import ChatRequest
from utils.response import fail, ResponseCode, ResponseMessage
from service.app_service import chat, prepare_stream_chat

router = APIRouter()


@router.post("/v1/chat/completions")
async def llm_chat(request: ChatRequest):
    if request.stream:
        try:
            gen = await prepare_stream_chat(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                model=request.model,
            )
        except Exception as e:
            return JSONResponse(
                content=fail(
                    message=str(e) or ResponseMessage.BUSINESS_FAIL,
                    code=ResponseCode.BUSINESS_FAIL,
                ),
                status_code=ResponseCode.BUSINESS_FAIL,
            )

        return StreamingResponse(
            gen,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        result = await chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model,
        )
        return JSONResponse(content=result)
