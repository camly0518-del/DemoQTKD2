"""
Cấu hình và Quy tắc nghiệp vụ (Business Rules) cho AI Agent Công ty Minh An
"""

# Cấu hình API Key (Google Gemini API)
GEMINI_API_KEY = "AQ.Ab8RN6KMH9ZN5fN72e1cmimg53tYL7U-4kUJPaR535VmgBkH2A"
GEMINI_MODEL = "gemini-3.8-flash"

# Danh sách Nhân viên Kinh doanh (6 NVKD theo bối cảnh Minh An)
SALES_REPS = [
    {"id": "NV01", "name": "Nguyễn Văn An", "email": "an.nv@minhan.com.vn"},
    {"id": "NV02", "name": "Trần Thị Bích", "email": "bich.tt@minhan.com.vn"},
    {"id": "NV03", "name": "Lê Hoàng Cường", "email": "cuong.lh@minhan.com.vn"},
    {"id": "NV04", "name": "Phạm Minh Đức", "email": "duc.pm@minhan.com.vn"},
    {"id": "NV05", "name": "Hoàng Thu Giang", "email": "giang.ht@minhan.com.vn"},
    {"id": "NV06", "name": "Vũ Hải Yến", "email": "yen.vh@minhan.com.vn"},
]

# Trưởng phòng Kinh doanh (Approver)
SALES_MANAGER = {
    "id": "TP01",
    "name": "Đặng Quốc Hưng (Trưởng phòng KD)",
    "email": "hung.dq@minhan.com.vn"
}

# Quy tắc phân quyền & Chiết khấu (Policy Engine Rules)
POLICY_RULES = {
    # Hạn mức thẩm quyền NVKD
    "MAX_REP_DEAL_VALUE": 300_000_000,    # Đơn hàng <= 300 triệu VNĐ: NVKD được tự quyết
    "MAX_REP_DISCOUNT_PERCENT": 5.0,      # Chiết khấu <= 5.0%: NVKD được tự quyết

    # Bậc thang chiết khấu tiêu chuẩn theo giá trị đơn hàng trước chiết khấu
    "DISCOUNT_TIERS": [
        {"min_value": 0, "max_value": 50_000_000, "standard_discount": 0.0},
        {"min_value": 50_000_000, "max_value": 150_000_000, "standard_discount": 3.0},
        {"min_value": 150_000_000, "max_value": 300_000_000, "standard_discount": 5.0},
        {"min_value": 300_000_000, "max_value": 999_999_999_999, "standard_discount": 8.0}, # Cần duyệt TP
    ],

    # Quy tắc an toàn (Guardrails)
    "REQUIRED_FIELDS": ["customer_name", "items", "expected_deadline_days"],
    # Nếu thiếu ngân sách (budget), agent xếp vào diện cần xác nhận ngân sách hoặc tư vấn theo khung giá
}

# Trạng thái cơ hội bán hàng chuẩn hóa
STATUS_QUALIFIED = "Có thể tiếp tục"       # Đủ dữ kiện, đáp ứng kho, trong thẩm quyền
STATUS_NEEDS_INFO = "Cần bổ sung thông tin" # Thiếu sản phẩm, thiếu số lượng, thiếu deadline hoặc thông tin liên hệ
STATUS_INFEASIBLE = "Chưa đáp ứng"        # Kho không đủ, lead time không kịp, vượt xa ngân sách
STATUS_PENDING_APPROVAL = "Chờ duyệt"     # Vượt thẩm quyền NVKD (>300tr, chiết khấu > 5%, hoặc ngoại lệ)

