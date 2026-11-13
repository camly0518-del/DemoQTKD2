"""
Module nạp dữ liệu đa kênh cho AI Agent Minh An:
- File Excel (.xlsx, .xls)
- File CSV (.csv)
- Đường dẫn Google Sheets (tự động phân tích và fetch dữ liệu trực tiếp)
- Bộ dữ liệu mẫu tích hợp sẵn phục vụ thi cử & kiểm thử tức thì
"""

import re
import io
import requests
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any

# Bảng ánh xạ tiêu chuẩn cột (Standard Column Synonyms)
COLUMN_ALIASES = {
    "request_id": ["request_id", "mã yêu cầu", "mã yc", "id", "stt", "mã đơn", "mã"],
    "customer_name": ["customer_name", "tên khách hàng", "khách hàng", "doanh nghiệp", "tên cty", "công ty", "client"],
    "contact_email": ["contact_email", "email", "liên hệ", "số điện thoại", "điện thoại", "sđt", "phone", "contact"],
    "items_text": ["items_text", "items", "hạng mục", "sản phẩm", "danh mục thiết bị", "yêu cầu", "thiết bị", "hàng hóa"],
    "budget": ["budget", "ngân sách", "ngân sách dự kiến", "kinh phí", "budget_vnd"],
    "expected_deadline_days": ["expected_deadline_days", "thời hạn", "thời hạn (ngày)", "deadline", "thời gian", "tiến độ"],
    "requested_discount_percent": ["requested_discount_percent", "chiết khấu yêu cầu", "chiết khấu (%)", "chiết khấu", "discount", "ck"],
    "notes": ["notes", "ghi chú", "yêu cầu thêm", "mô tả", "chi tiết"]
}

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Tự động chuẩn hóa tên cột linh hoạt để thích ứng mọi bộ test của giảng viên"""
    col_mapping = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        matched = False
        for std_col, aliases in COLUMN_ALIASES.items():
            if c_clean in aliases or any(alias in c_clean for alias in aliases):
                col_mapping[col] = std_col
                matched = True
                break
        if not matched:
            col_mapping[col] = c_clean

    df_renamed = df.rename(columns=col_mapping)

    # Đảm bảo các cột tối thiểu tồn tại
    for std_col in COLUMN_ALIASES.keys():
        if std_col not in df_renamed.columns:
            df_renamed[std_col] = None

    return df_renamed

def load_from_csv(file_obj_or_path) -> Tuple[Optional[pd.DataFrame], str]:
    """Đọc dữ liệu từ file CSV"""
    try:
        # Thử các loại encoding phổ biến
        try:
            df = pd.read_csv(file_obj_or_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_obj_or_path, encoding="utf-8-sig")
        df_norm = normalize_column_names(df)
        return df_norm, f"Tải thành công {len(df_norm)} bản ghi từ CSV."
    except Exception as e:
        return None, f"Lỗi đọc file CSV: {str(e)}"

def load_from_excel(file_obj_or_path) -> Tuple[Optional[pd.DataFrame], str]:
    """Đọc dữ liệu từ file Excel (.xlsx, .xls)"""
    try:
        df = pd.read_excel(file_obj_or_path)
        df_norm = normalize_column_names(df)
        return df_norm, f"Tải thành công {len(df_norm)} bản ghi từ Excel."
    except Exception as e:
        return None, f"Lỗi đọc file Excel: {str(e)}"

def load_from_google_sheets(url: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Đọc dữ liệu từ link Google Sheets công khai.
    Hỗ trợ tự động chuyển đổi URL sang link export CSV trực tiếp.
    """
    if not url or not str(url).strip():
        return None, "Đường dẫn Google Sheets không được để trống."

    url = url.strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        return None, "Đường dẫn không hợp lệ. Vui lòng cung cấp link dạng: https://docs.google.com/spreadsheets/d/{ID}/edit"

    sheet_id = match.group(1)

    # Tìm gid (sheet con) nếu có
    gid_match = re.search(r"[#&]gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(export_url, headers=headers, timeout=15)
        if resp.status_code == 200 and resp.content:
            content_str = resp.content.decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(content_str))
            df_norm = normalize_column_names(df)
            return df_norm, f"Tải thành công {len(df_norm)} bản ghi từ Google Sheets."
        elif resp.status_code == 403 or "accounts.google.com" in resp.url:
            return None, "Không thể truy cập Google Sheet. Vui lòng mở quyền 'Bất kỳ ai có đường liên kết đều có thể xem' (Anyone with the link can view)."
        else:
            return None, f"Lỗi từ Google Sheets server (HTTP {resp.status_code})."
    except Exception as e:
        return None, f"Lỗi kết nối tới Google Sheets: {str(e)}"


def get_default_sample_dataframe() -> pd.DataFrame:
    """
    Tạo bộ dữ liệu mẫu chuẩn đề thi AI301, bao gồm:
    - 2 trường hợp thông thường (Qualified)
    - 2 trường hợp thiếu thông tin (Needs Info)
    - 2 trường hợp không đáp ứng được (Infeasible: hết kho / lead time gấp)
    - 2 trường hợp ranh giới quy tắc / vượt thẩm quyền (Pending Approval: chiết khấu cao, deal >300M, thiếu ngân sách)
    """
    data = [
        # 1. Trường hợp thông thường 1: Đầy đủ, trong thẩm quyền
        {
            "request_id": "YC-001",
            "customer_name": "Công ty TNHH Giải pháp FPT Smart",
            "contact_email": "procurement@fptsmart.vn",
            "items_text": "2x Cisco Catalyst 9200L 24P; 1x Dịch vụ lắp đặt và cấu hình cơ bản",
            "budget": 100_000_000,
            "expected_deadline_days": 10,
            "requested_discount_percent": 3.0,
            "notes": "Cần hoàn thiện triển khai văn phòng mới trước ngày 25."
        },
        # 2. Trường hợp thông thường 2: Đơn nhỏ, kho sẵn
        {
            "request_id": "YC-002",
            "customer_name": "Ngân hàng Thương mại Việt Á",
            "contact_email": "it_infra@vietabank.com.vn",
            "items_text": "5x Aruba AP-505; 1x APC Smart-UPS 3000VA",
            "budget": 95_000_000,
            "expected_deadline_days": 7,
            "requested_discount_percent": 3.0,
            "notes": "Yêu cầu giao hàng giờ hành chính kèm biên bản CO/CQ."
        },
        # 3. Trường hợp thiếu dữ liệu 1: Thiếu ngân sách & số lượng
        {
            "request_id": "YC-003",
            "customer_name": "Công ty Cổ phần Vận tải Biển Đông",
            "contact_email": "info@biendongmaritime.com",
            "items_text": "Máy chủ Dell PowerEdge R750; Switch Cisco",
            "budget": 0,
            "expected_deadline_days": 15,
            "requested_discount_percent": 0.0,
            "notes": "Cần tư vấn cấu hình và báo giá gấp, chưa có ngân sách cụ thể."
        },
        # 4. Trường hợp thiếu dữ liệu 2: Thiếu thời hạn & người liên hệ chưa rõ email
        {
            "request_id": "YC-004",
            "customer_name": "Tập đoàn Đầu tư Alpha",
            "contact_email": "",
            "items_text": "1x FortiGate 100F; 2x Cisco Catalyst 9200L 24P",
            "budget": 160_000_000,
            "expected_deadline_days": 0,
            "requested_discount_percent": 5.0,
            "notes": "Gửi qua hotline không để lại email liên hệ trực tiếp."
        },
        # 5. Trường hợp không đáp ứng được 1: Hết kho & deadline quá gấp
        {
            "request_id": "YC-005",
            "customer_name": "Bệnh viện Đa khoa Quốc tế Hoàn Mỹ",
            "contact_email": "it@hoanmyhospital.vn",
            "items_text": "10x Máy chủ HPE ProLiant DL380 Gen10",
            "budget": 1_500_000_000,
            "expected_deadline_days": 3,
            "requested_discount_percent": 5.0,
            "notes": "Cần giao ngay trong 3 ngày để kịp nghiệm thu dự án Bộ Y tế (Kho chỉ còn 3 chiếc, cần 18 ngày)."
        },
        # 6. Trường hợp không đáp ứng được 2: Sản phẩm không có trong Catalog
        {
            "request_id": "YC-006",
            "customer_name": "Trường Quốc tế Sky Academy",
            "contact_email": "admin@skyacademy.edu.vn",
            "items_text": "20x Máy in Canon Laser LBP2900; 1x Switch Cisco 9200L",
            "budget": 100_000_000,
            "expected_deadline_days": 10,
            "requested_discount_percent": 0.0,
            "notes": "Công ty Minh An chỉ cung cấp hạ tầng máy chủ và mạng, không phân phối máy in Canon."
        },
        # 7. Trường hợp ranh giới quy tắc 1: Vượt thẩm quyền giá trị (> 300 triệu) & Chiết khấu cao (8%)
        {
            "request_id": "YC-007",
            "customer_name": "Công ty CP Logistics Tân Cảng",
            "contact_email": "muahang@tancanglogistics.com",
            "items_text": "3x Dell PowerEdge R750; 2x Cisco Catalyst 9300 48P; 1x Dịch vụ triển khai và di chuyển hệ thống nâng cao",
            "budget": 650_000_000,
            "expected_deadline_days": 20,
            "requested_discount_percent": 8.0,
            "notes": "Khách hàng VIP, yêu cầu chiết khấu 8% theo đơn hàng lớn (khoảng 640 triệu). Vượt quyền NVKD."
        },
        # 8. Trường hợp ranh giới quy tắc 2: Đòi chiết khấu 10% (vượt mức tối đa 5%)
        {
            "request_id": "YC-008",
            "customer_name": "Công ty TNHH Bất động sản Phú Thịnh",
            "contact_email": "duan@phuthinhland.com",
            "items_text": "2x FortiGate 100F; 4x Cisco Catalyst 9200L 24P",
            "budget": 280_000_000,
            "expected_deadline_days": 14,
            "requested_discount_percent": 10.0,
            "notes": "Đơn hàng 298 triệu nhưng khách đòi chiết khấu 10% mới chịu ký. Cần Trưởng phòng phê duyệt."
        }
    ]
    return normalize_column_names(pd.DataFrame(data))

