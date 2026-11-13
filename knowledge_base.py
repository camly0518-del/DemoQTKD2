"""
Cơ sở dữ liệu tri thức của Công ty Minh An:
1. Danh mục sản phẩm & Bảng giá chuẩn (Catalog & Pricing)
2. Tồn kho khả dụng & Thời gian cung ứng (Inventory & Lead-time)
3. Các hàm công cụ tra cứu nghiệp vụ (Tools)
"""

import pandas as pd
from typing import Dict, List, Optional, Any

# 1. Danh mục sản phẩm & Bảng giá chuẩn niêm yết (Cập nhật mới nhất Q1/2026)
CATALOG_DATA = [
    {
        "sku": "SRV-DELL-R750",
        "name": "Máy chủ Dell PowerEdge R750",
        "category": "Máy chủ & Lưu trữ",
        "unit": "Hệ thống",
        "list_price": 145_000_000,
        "description": "Server 2U, Intel Xeon Silver 4314, 64GB RAM, 2x 960GB SSD SAS",
        "warranty_months": 36
    },
    {
        "sku": "SRV-HPE-DL380",
        "name": "Máy chủ HPE ProLiant DL380 Gen10",
        "category": "Máy chủ & Lưu trữ",
        "unit": "Hệ thống",
        "list_price": 138_000_000,
        "description": "Server 2U, Intel Xeon Silver 4210R, 32GB RAM, 2x 1.2TB SAS",
        "warranty_months": 36
    },
    {
        "sku": "SW-CISCO-C9200",
        "name": "Thiết bị chuyển mạch Cisco Catalyst 9200L 24P",
        "category": "Thiết bị Mạng",
        "unit": "Chiếc",
        "list_price": 38_500_000,
        "description": "24 cổng Gigabit PoE+, 4x 10G SFP+ uplink, Network Essentials",
        "warranty_months": 24
    },
    {
        "sku": "SW-CISCO-C9300",
        "name": "Thiết bị chuyển mạch Cisco Catalyst 9300 48P",
        "category": "Thiết bị Mạng",
        "unit": "Chiếc",
        "list_price": 86_000_000,
        "description": "48 cổng Gigabit PoE+, mô-đun nguồn kép, Network Advantage",
        "warranty_months": 24
    },
    {
        "sku": "FW-FORTI-100F",
        "name": "Tường lửa Fortinet FortiGate 100F",
        "category": "An toàn Thông tin",
        "unit": "Thiết bị",
        "list_price": 72_000_000,
        "description": "Bảo vệ mạng doanh nghiệp 100-300 users, bundle 1 năm UTP license",
        "warranty_months": 24
    },
    {
        "sku": "AP-ARUBA-AP505",
        "name": "Bộ phát WiFi Aruba AP-505 (Wi-Fi 6)",
        "category": "Thiết bị Mạng",
        "unit": "Chiếc",
        "list_price": 9_800_000,
        "description": "Access Point Dual-band 2x2:2 Wi-Fi 6 chuẩn 802.11ax",
        "warranty_months": 12
    },
    {
        "sku": "UPS-APC-3KVA",
        "name": "Bộ lưu điện APC Smart-UPS 3000VA LCD RM 2U",
        "category": "Thiết bị Phụ trợ",
        "unit": "Chiếc",
        "list_price": 42_000_000,
        "description": "UPS 2700W/3000VA, dạng rackmount 2U, sóng sine chuẩn",
        "warranty_months": 24
    },
    {
        "sku": "SVC-DEPLOY-BASIC",
        "name": "Dịch vụ lắp đặt và cấu hình cơ bản",
        "category": "Dịch vụ Kỹ thuật",
        "unit": "Gói",
        "list_price": 15_000_000,
        "description": "Triển khai tại chỗ, cấu hình mạng cơ bản, kiểm thử vận hành",
        "warranty_months": 6
    },
    {
        "sku": "SVC-DEPLOY-ADV",
        "name": "Dịch vụ triển khai và di chuyển hệ thống nâng cao",
        "category": "Dịch vụ Kỹ thuật",
        "unit": "Gói",
        "list_price": 35_000_000,
        "description": "Cấu hình bảo mật chuyên sâu, HA clustering, tài liệu chuyển giao",
        "warranty_months": 12
    },
    {
        "sku": "LIC-VMWARE-STD",
        "name": "License VMware vSphere Standard 1 CPU",
        "category": "Phần mềm Bản quyền",
        "unit": "License",
        "list_price": 28_000_000,
        "description": "Bản quyền ảo hóa cho 1 vi xử lý vật lý kèm 1 năm SnS",
        "warranty_months": 12
    }
]

# 2. Dữ liệu Vận hành: Tồn kho tức thì & Lead-time cung ứng
INVENTORY_DATA = {
    "SRV-DELL-R750": {"available_stock": 5, "restock_lead_time_days": 14, "sla_delivery_days": 3},
    "SRV-HPE-DL380": {"available_stock": 3, "restock_lead_time_days": 18, "sla_delivery_days": 3},
    "SW-CISCO-C9200": {"available_stock": 12, "restock_lead_time_days": 7, "sla_delivery_days": 2},
    "SW-CISCO-C9300": {"available_stock": 4, "restock_lead_time_days": 15, "sla_delivery_days": 3},
    "FW-FORTI-100F": {"available_stock": 6, "restock_lead_time_days": 10, "sla_delivery_days": 2},
    "AP-ARUBA-AP505": {"available_stock": 30, "restock_lead_time_days": 5, "sla_delivery_days": 1},
    "UPS-APC-3KVA": {"available_stock": 8, "restock_lead_time_days": 10, "sla_delivery_days": 2},
    "SVC-DEPLOY-BASIC": {"available_stock": 999, "restock_lead_time_days": 0, "sla_delivery_days": 2},
    "SVC-DEPLOY-ADV": {"available_stock": 999, "restock_lead_time_days": 0, "sla_delivery_days": 5},
    "LIC-VMWARE-STD": {"available_stock": 999, "restock_lead_time_days": 0, "sla_delivery_days": 1},
}

class KnowledgeBase:
    """Quản lý tra cứu dữ liệu danh mục, giá niêm yết và tồn kho của Công ty Minh An"""

    @classmethod
    def get_catalog_df(cls) -> pd.DataFrame:
        rows = []
        for item in CATALOG_DATA:
            sku = item["sku"]
            inv = INVENTORY_DATA.get(sku, {"available_stock": 0, "restock_lead_time_days": 30, "sla_delivery_days": 7})
            row = {**item, **inv}
            rows.append(row)
        return pd.DataFrame(rows)

    @classmethod
    def find_product_by_query(cls, query_text: str) -> Optional[Dict[str, Any]]:
        """
        Tool tra cứu sản phẩm thông minh dựa vào SKU hoặc Tên sản phẩm.
        Hỗ trợ tìm kiếm xấp xỉ không phân biệt hoa thường.
        """
        if not query_text:
            return None
        q = str(query_text).strip().lower()

        # 1. Tìm chính xác SKU
        for item in CATALOG_DATA:
            if item["sku"].lower() == q:
                return item

        # 2. Tìm theo từ khóa trong SKU hoặc tên
        for item in CATALOG_DATA:
            if q in item["sku"].lower() or item["sku"].lower() in q:
                return item
            if q in item["name"].lower() or item["name"].lower() in q:
                return item

        # 3. Fuzzy keyword matching
        keywords = q.replace("-", " ").replace("/", " ").split()
        best_match = None
        max_matches = 0
        for item in CATALOG_DATA:
            target_str = (item["sku"] + " " + item["name"] + " " + item["description"]).lower()
            matches = sum(1 for kw in keywords if len(kw) >= 3 and kw in target_str)
            if matches > max_matches and matches >= 2:
                max_matches = matches
                best_match = item

        return best_match

    @classmethod
    def check_inventory_and_sla(cls, sku: str, requested_qty: int, requested_days: Optional[int]) -> Dict[str, Any]:
        """
        Tool thẩm định năng lực đáp ứng của Bộ phận Vận hành:
        - So sánh số lượng cần vs Tồn kho khả dụng
        - So sánh thời hạn khách yêu cầu vs SLA giao hàng / thời gian nhập kho
        """
        inv = INVENTORY_DATA.get(sku)
        if not inv:
            return {
                "sku": sku,
                "found": False,
                "is_stock_available": False,
                "available_stock": 0,
                "min_lead_time_days": 30,
                "lead_time_feasible": False,
                "reason": f"Mã sản phẩm {sku} chưa được định nghĩa trong hệ thống Vận hành."
            }

        stock = inv["available_stock"]
        sla_standard = inv["sla_delivery_days"]
        restock_lead = inv["restock_lead_time_days"]

        # Nếu đủ hàng trong kho: thời gian giao = SLA tiêu chuẩn
        # Nếu thiếu hàng trong kho: thời gian = restock_lead + sla_delivery_days
        is_in_stock = stock >= requested_qty
        min_lead_time = sla_standard if is_in_stock else (restock_lead + sla_standard)

        lead_time_feasible = True
        reason_parts = []

        if not is_in_stock:
            reason_parts.append(f"Kho chỉ còn {stock}/{requested_qty} sản phẩm (thiếu {requested_qty - stock}). Cần thời gian nhập hàng {restock_lead} ngày.")

        if requested_days is not None and requested_days > 0:
            if requested_days < min_lead_time:
                lead_time_feasible = False
                reason_parts.append(f"Thời hạn khách mong muốn ({requested_days} ngày) ngắn hơn thời gian tối thiểu khả dụng ({min_lead_time} ngày).")
            else:
                reason_parts.append(f"Thời hạn khách yêu cầu ({requested_days} ngày) đáp ứng được (tối thiểu {min_lead_time} ngày).")
        else:
            reason_parts.append(f"Thời gian triển khai dự kiến: {min_lead_time} ngày làm việc.")

        return {
            "sku": sku,
            "found": True,
            "available_stock": stock,
            "requested_qty": requested_qty,
            "is_stock_available": is_in_stock,
            "min_lead_time_days": min_lead_time,
            "lead_time_feasible": lead_time_feasible,
            "details": "; ".join(reason_parts)
        }

