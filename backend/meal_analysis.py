from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, UploadFile, status

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB hard limit


async def read_image_bytes(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng ảnh không được hỗ trợ. Hãy dùng JPG, PNG hoặc WebP.",
        )
    data = await upload.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Không nhận được dữ liệu ảnh."
        )
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ảnh vượt quá giới hạn 8MB, vui lòng nén hoặc chụp lại.",
        )
    return data


def detect_follow_up_need(response_text: Optional[str]) -> bool:
    if not response_text:
        return True
    normalized = response_text.lower()
    return "?" in normalized or "vui lòng" in normalized or "hãy" in normalized

