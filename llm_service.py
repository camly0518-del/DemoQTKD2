"""
Dịch vụ gọi mô hình ngôn ngữ lớn Google Gemini (LLM Service)
Tích hợp API Key của người dùng để nâng cao năng lực bóc tách văn bản tự nhiên,
phân tích cơ hội kinh doanh và cá nhân hóa email phản hồi khách hàng.
"""

import requests
import json
from typing import Optional, Dict, Any
from config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiLLMService:
    API_KEY = GEMINI_API_KEY
    MODEL = GEMINI_MODEL
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    @classmethod
    def generate_text(cls, prompt: str, temperature: float = 0.2, timeout: int = 8) -> Optional[str]:
        """Gọi Gemini API để sinh văn bản / phân tích"""
        if not cls.API_KEY or cls.API_KEY.startswith("YOUR_"):
            return None

        url = f"{cls.BASE_URL}/{cls.MODEL}:generateContent?key={cls.API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            return None
        except Exception:
            return None

    @classmethod
    def enhance_customer_email(cls, standard_email: str, customer_name: str, context_notes: str) -> str:
        """Sử dụng Gemini để làm mượt mà và cá nhân hóa email phản hồi"""
        if not context_notes:
            return standard_email

        prompt = f"""Bạn là Chuyên viên Kinh doanh B2B cao cấp của Công ty Công nghệ Minh An.
Hãy tinh chỉnh lại email dưới đây sao cho chuyên nghiệp, lịch sự, đúng chuẩn phong cách B2B nhưng tự nhiên, ngắn gọn và giải quyết trực tiếp ghi chú/nhu cầu của khách hàng:
- Khách hàng: {customer_name}
- Ghi chú khách hàng: {context_notes}
- Email gốc:
{standard_email}

Chỉ trả về nội dung email hoàn chỉnh, không kèm lời dẫn giải thích.
"""
        result = cls.generate_text(prompt, temperature=0.3, timeout=6)
        return result if result else standard_email

