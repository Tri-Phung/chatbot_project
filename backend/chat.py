from __future__ import annotations

import re
from typing import Dict, List, Optional

Message = Dict[str, str]


PLAN_KEYWORDS = [
    "kế hoạch",
    "lịch tập",
    "workout",
    "tập luyện",
    "chương trình tập",
    "plan",
    "routine",
    "thực đơn",
    "meal plan",
    "chế độ ăn",
    "nutrition plan",
]

FIELD_PATTERNS = {
    "goal": ["tăng cơ", "giảm mỡ", "giữ form", "giữ dáng", "giảm cân", "lean"],
    "experience": ["mới tập", "newbie", "trung cấp", "nâng cao", "advanced", "beginner"],
    "equipment": ["không dụng cụ", "bodyweight", "dụng cụ", "tạ", "gym", "dumbbell", "resistance"],
    "schedule": ["ngày", "buổi", "lịch", "tuần"],
    "limitations": ["đau", "chấn thương", "hạn chế", "không thể", "tránh"],
    "diet": ["ăn chay", "eat clean", "ít carb", "đạm cao", "thuần chay", "keto", "mediterranean"],
}

FIELD_LABELS_VI = {
    "goal": "mục tiêu (tăng cơ/giảm mỡ/giữ form)",
    "experience": "trình độ tập luyện",
    "equipment": "dụng cụ sẵn có",
    "schedule": "số buổi/tuần bạn có thể tập",
    "limitations": "giới hạn vận động hoặc vùng bị đau (không nêu chi tiết bệnh lý)",
    "diet": "khẩu vị hoặc chế độ ăn ưu tiên",
    "body_metrics": "cân nặng, chiều cao, độ tuổi",
}


def _has_body_metrics(text: str) -> bool:
    return bool(re.search(r"\b\d{2,3}\s?(kg|kilô|kgm?)\b", text)) or bool(
        re.search(r"\b\d{3}\s?cm\b", text)
    ) or "tuổi" in text


def _field_present(field: str, text: str) -> bool:
    if field == "body_metrics":
        return _has_body_metrics(text)
    patterns = FIELD_PATTERNS.get(field, [])
    return any(pattern in text for pattern in patterns)


def detect_plan_request(messages: List[Message]) -> bool:
    for message in messages:
        if message.get("role") != "user":
            continue
        text = message.get("content", "").lower()
        if any(keyword in text for keyword in PLAN_KEYWORDS):
            return True
    return False


def evaluate_missing_fields(messages: List[Message]) -> List[str]:
    status = {field: False for field in FIELD_LABELS_VI}
    for message in messages:
        if message.get("role") != "user":
            continue
        text = message.get("content", "").lower()
        for field in status:
            if not status[field] and _field_present(field, text):
                status[field] = True
    return [field for field, present in status.items() if not present]


def build_clarification_prompt(missing_fields: List[str]) -> str:
    if not missing_fields:
        return ""
    lines = [
        "Để mình cá nhân hóa kế hoạch chuẩn xác và tránh đoán mò, mình cần bạn bổ sung:"
    ]
    for field in missing_fields:
        label = FIELD_LABELS_VI[field]
        lines.append(f"- {label}")
    lines.append("Hãy trả lời từng mục, mình sẽ tiếp tục tư vấn ngay sau khi nhận đủ thông tin nhé!")
    return "\n".join(lines)


def guard_chat_request(messages: List[Message]) -> Optional[str]:
    plan_related = detect_plan_request(messages)
    if not plan_related:
        return None
    missing = evaluate_missing_fields(messages)
    if not missing:
        return None
    return build_clarification_prompt(missing)

