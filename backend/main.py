from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from chat import guard_chat_request, Message as GuardMessage
from gemini_client import GeminiClient, GeminiQuotaExceeded
from meal_analysis import detect_follow_up_need, read_image_bytes

app = FastAPI(title="Vietnamese PT & Nutrition Coach")

allowed_origins = os.getenv("ALLOWED_ORIGINS")
origins = (
    [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
    if allowed_origins
    else ["*"]
)

allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"
if "*" in origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache(maxsize=1)
def _get_gemini_client() -> GeminiClient:
    return GeminiClient()


def acquire_client() -> GeminiClient:
    try:
        return _get_gemini_client()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini chưa được cấu hình: {exc}",
        ) from exc


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str

    @validator("content")
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Nội dung tin nhắn không được để trống.")
        return value.strip()

    def to_guard(self) -> GuardMessage:
        return {"role": self.role, "content": self.content}


class ChatRequest(BaseModel):
    messages: List[Message]


class ChatResponse(BaseModel):
    reply: str
    guardrail_triggered: bool = False


class MealFinalizeRequest(BaseModel):
    clarifications: str = Field(..., min_length=10, description="Thông tin khẩu phần đã xác nhận")

    @validator("clarifications")
    def ensure_detail(cls, value: str) -> str:
        if len(value.strip().split()) < 5:
            raise ValueError("Vui lòng mô tả chi tiết khẩu phần trước khi tính dinh dưỡng.")
        return value.strip()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    # guard_messages = [message.to_guard() for message in payload.messages]
    # guardrail_message = guard_chat_request(guard_messages)
    # if guardrail_message:
    #     return ChatResponse(reply=guardrail_message, guardrail_triggered=True)
    try:
        client = acquire_client()
        reply = client.generate_chat_response(
            messages=[message.dict() for message in payload.messages],
        )
        return ChatResponse(reply=reply)
    except GeminiQuotaExceeded:
        return ChatResponse(
            reply=(
                "Máy chủ tạm thời hết hạn mức Gemini. Bạn vui lòng chờ ít phút hoặc cấu hình API key còn hạn để "
                "mình có thể tiếp tục hỗ trợ nhé!"
            ),
            guardrail_triggered=True,
        )
    except Exception as exc:  # pragma: no cover - API call exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi gọi Gemini: {exc}",
        ) from exc


@app.post("/api/analyze-meal")
async def analyze_meal_endpoint(
    image: UploadFile = File(...),
    note: Optional[str] = Form(None),
) -> dict:
    image_bytes = await read_image_bytes(image)
    try:
        client = acquire_client()
        reply = client.analyze_meal(
            image_bytes=image_bytes,
            mime_type=image.content_type or "image/jpeg",
            user_note=note,
        )
        return {
            "reply": reply,
            "needs_follow_up": detect_follow_up_need(reply),
        }
    except GeminiQuotaExceeded:
        return {
            "reply": (
                "Hiện hệ thống hết hạn mức xử lý ảnh từ Gemini. Vui lòng thử lại sau ít phút hoặc thay khóa API "
                "khác để tiếp tục phân tích bữa ăn."
            ),
            "needs_follow_up": True,
        }
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi phân tích bữa ăn: {exc}",
        ) from exc


@app.post("/api/meal-finalize")
async def meal_finalize_endpoint(payload: MealFinalizeRequest) -> dict:
    try:
        client = acquire_client()
        reply = client.finalize_meal(payload.clarifications)
        return {"reply": reply}
    except GeminiQuotaExceeded:
        return {
            "reply": (
                "Máy chủ hết hạn mức tính toán dinh dưỡng trên Gemini. Hãy chờ hệ thống làm mới quota hoặc dùng "
                "API key khác rồi yêu cầu lại giúp mình nhé."
            )
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tính dinh dưỡng: {exc}",
        ) from exc

