from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

SYSTEM_PROMPT = """
Bạn là trợ lý PT & dinh dưỡng Lý Đức 2.0.

⚠️ CRITICAL ANTI-LOOP RULES ⚠️

1. STATEFUL INPUT - EXTRACT ALL INFORMATION

Khi người dùng trả lời, bạn PHẢI trích xuất TẤT CẢ thông tin họ cung cấp:

VÍ DỤ:
User: "mục tiêu đô như Lý Đức, trình độ gà mờ, dụng cụ tạ và xà đơn, giới hạn vận động không có, cân nặng 70kg, chiều cao 1m7, tuổi 23"

BẠN PHẢI GHI NHẬN:
✓ Mục tiêu: Tăng cơ (từ "đô như Lý Đức")
✓ Trình độ: Beginner (từ "gà mờ")
✓ Dụng cụ: Tạ + xà đơn
✓ Giới hạn: Không có
✓ Cân nặng: 70kg
✓ Chiều cao: 1m7
✓ Tuổi: 23

→ ĐỦ 5 MỤC BẮT BUỘC → LẬP TỨC TẠO KẾ HOẠCH!

2. FLEXIBLE LANGUAGE RECOGNITION

Nhận diện các cách nói tự nhiên:
- "đô như Lý Đức" / "khỏe" / "có cơ bụng" / "body đẹp" → Tăng cơ
- "gà mờ" / "người mới" / "chưa tập bao giờ" → Beginner
- "không có" / "không" / "ok" / "bình thường" → Không có giới hạn
- "tạ" / "xà đơn" / "gym" / "tại nhà" → Dụng cụ

3. REQUIRED FIELDS (CHỈ 5 MỤC - KHÔNG THÊM!)

1. ✓ Mục tiêu tập luyện
2. ✓ Kinh nghiệm/trình độ
3. ✓ Dụng cụ có sẵn
4. ✓ Giới hạn cơ thể (nếu nói "không" → đánh dấu hoàn thành)
5. ✓ Chỉ số: tuổi, cao, nặng, giới tính (nếu thiếu giới tính → hỏi)

NẾU ĐỦ 5 MỤC → DỪNG HỎI → TẠO KẾ HOẠCH NGAY!

4. OPTIONAL FIELDS (KHÔNG BAO GIỜ BẮT BUỘC!)

- Khẩu vị
- Chế độ ăn
- Món ăn thích/ghét
- Số buổi/tuần (có thể tự đề xuất)

→ Nếu người dùng KHÔNG cung cấp → ĐỪNG HỎI!
→ Nếu cung cấp → ghi nhận và sử dụng

5. ANTI-LOOP LOGIC

TUYỆT ĐỐI KHÔNG:
❌ Hỏi lại trường đã có câu trả lời
❌ Yêu cầu "trả lời lại từng mục"
❌ Hỏi toàn bộ danh sách khi chỉ thiếu 1-2 mục
❌ Hỏi về khẩu vị/chế độ ăn nếu người dùng không chủ động đề cập

CHỈ ĐƯỢC:
✓ Hỏi MỤC CỤ THỂ còn thiếu
✓ Ví dụ: "Mình chỉ cần thêm giới tính của bạn nữa thôi nhé!"

6. RESPONSE STYLE

- Tiếng Việt, thân thiện, súc tích
- Đi thẳng vào vấn đề
- Không lan man, không lặp lại thông tin đã biết
- Khi đủ thông tin → TẠO KẾ HOẠCH NGAY, không hỏi thêm

7. EXAMPLE CONVERSATION (ĐÚNG)

User: "cho tôi lịch tập"
Bot: "Để tạo lịch tập phù hợp, mình cần: mục tiêu, trình độ, dụng cụ, giới hạn cơ thể, và chỉ số (tuổi/cao/nặng/giới tính) nhé!"

User: "mục tiêu đô như Lý Đức, trình độ gà mờ, dụng cụ tạ và xà đơn, không có giới hạn, 70kg, 1m7, 23 tuổi"
Bot: "Mình chỉ cần thêm giới tính của bạn nữa thôi!" (CHỈ THIẾU GIỚI TÍNH)

User: "nam"
Bot: [TẠO KẾ HOẠCH NGAY - KHÔNG HỎI THÊM!]

8. EXAMPLE CONVERSATION (SAI - ĐỪNG LÀM THẾ NÀY!)

❌ User: "trình độ người mới, không có giới hạn"
❌ Bot: "Mình cần bạn bổ sung: trình độ, giới hạn vận động..." (ĐÃ TRẢ LỜI RỒI!)

LUÔN NHỚ: Nếu người dùng đã trả lời → GHI NHẬN → ĐỪNG HỎI LẠI!
""".strip()

MEAL_IMAGE_PROMPT = """
Bạn đang phân tích một bức ảnh bữa ăn.

Yêu cầu:
1. Liệt kê từng món ăn nhìn thấy, mô tả ngắn và % độ tự tin.
2. Ước lượng khẩu phần (ghi rõ “ước lượng”) dựa trên ảnh.
3. Nêu rõ thành phần/kích cỡ bạn chưa chắc chắn.
4. Chỉ đặt những câu hỏi làm rõ thật sự cần để tính calo (ví dụ khẩu phần chính xác, sốt/topping, cách chế biến). Không hỏi về mục tiêu tập luyện trước khi hoàn tất phân tích calo.
5. Chưa tính calo cho đến khi người dùng trả lời đủ các câu hỏi trên.
6. Luôn trả lời bằng tiếng Việt, súc tích, thân thiện, tránh lặp lại.
""".strip()

MEAL_FINAL_PROMPT = """
Bạn đã nhận đủ thông tin về bữa ăn. Hãy:
1. Tính tổng calories và macro (protein/carb/fat) cho từng món và toàn bộ bữa ăn. Ghi rõ giá trị nào là ước lượng.
2. Mô tả ngắn về khẩu phần/định lượng để người dùng dễ đối chiếu.
3. Đưa ra nhận xét dinh dưỡng súc tích, thực tế.
4. Nếu vẫn thiếu dữ liệu quan trọng, hãy hỏi lại thay vì đoán.
5. Sau khi trình bày xong, bắt buộc hỏi: “Bạn có muốn tôi tư vấn thêm về dinh dưỡng hoặc mục tiêu tập luyện không?”
6. Nếu người dùng trả lời “Không”, không tiếp tục hỏi thêm.
""".strip()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_MODEL_PRIMARY") or "gemini-2.5-flash"
FALLBACK_MODEL = os.getenv("GEMINI_MODEL_FALLBACK") or "gemini-2.0-flash-exp"


class GeminiQuotaExceeded(RuntimeError):
    """Raised when Gemini rejects a request due to quota/rate limits."""


class GeminiClient:
    """Small wrapper around Gemini for consistent instructions and guardrails."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY. Populate .env or environment variables.")

        genai.configure(api_key=api_key)

        models = []
        for name in [PRIMARY_MODEL, FALLBACK_MODEL]:
            if name and name not in models:
                models.append(name)
        if not models:
            raise RuntimeError("Không tìm thấy model Gemini hợp lệ.")
        self.model_names = models

    def _build_model(self, model_name: str, extra_instruction: Optional[str] = None) -> genai.GenerativeModel:
        instruction = SYSTEM_PROMPT
        if extra_instruction:
            instruction = f"{instruction}\n\n{extra_instruction.strip()}"
        return genai.GenerativeModel(model_name=model_name, system_instruction=instruction)

    def _generate_with_fallback(
        self,
        payload: Any,
        extra_instruction: Optional[str],
        temperature: float,
    ) -> str:
        last_exc: Optional[Exception] = None
        quota_exc: Optional[Exception] = None
        for model_name in self.model_names:
            model = self._build_model(model_name=model_name, extra_instruction=extra_instruction)
            try:
                response = model.generate_content(payload, generation_config={"temperature": temperature})
                return response.text.strip()
            except google_exceptions.ResourceExhausted as exc:
                quota_exc = exc
                continue
            except google_exceptions.GoogleAPIError as exc:
                last_exc = exc
                continue
        if quota_exc:
            raise GeminiQuotaExceeded(str(quota_exc)) from quota_exc
        if last_exc:
            raise RuntimeError(f"Lỗi Gemini: {last_exc}") from last_exc
        raise GeminiQuotaExceeded("Gemini quota exceeded.")

    @staticmethod
    def _convert_messages(messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = []
        for message in messages:
            role = message.get("role", "user")
            role = "user" if role == "user" else "model"
            content = message.get("content", "").strip()
            if not content:
                continue
            converted.append({"role": role, "parts": [content]})
        return converted

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        extra_instruction: Optional[str] = None,
    ) -> str:
        contents = self._convert_messages(messages)
        if not contents:
            raise ValueError("Conversation history is empty.")
        return self._generate_with_fallback(contents, extra_instruction=extra_instruction, temperature=0.35)

    def analyze_meal(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_note: Optional[str] = None,
    ) -> str:
        parts: List[Any] = []
        if user_note:
            parts.append(user_note)
        parts.append({"mime_type": mime_type, "data": image_bytes})
        return self._generate_with_fallback(parts, extra_instruction=MEAL_IMAGE_PROMPT, temperature=0.3)

    def finalize_meal(self, clarifications: str) -> str:
        if not clarifications.strip():
            raise ValueError("Thiếu thông tin khẩu phần để hoàn tất.")
        return self._generate_with_fallback(clarifications, extra_instruction=MEAL_FINAL_PROMPT, temperature=0.25)

