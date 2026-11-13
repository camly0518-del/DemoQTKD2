"""
Bộ kiểm thử tự động (Automated Verification Test Suite)
Kiểm tra tính chính xác của các quy tắc nghiệp vụ, tính khả thi, phân quyền
và logic tạo hồ sơ theo yêu cầu của Đề tài AI301.
"""

import unittest
import pandas as pd
from config import (
    STATUS_QUALIFIED, STATUS_NEEDS_INFO, STATUS_INFEASIBLE, STATUS_PENDING_APPROVAL
)
from data_loader import get_default_sample_dataframe
from pipeline import SalesOpportunityPipeline
from knowledge_base import KnowledgeBase

class TestMinhAnAIAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = get_default_sample_dataframe()
        cls.dossiers, cls.summary = SalesOpportunityPipeline.process_dataframe(cls.df)
        cls.dossier_map = {d["request_id"]: d for d in cls.dossiers}

    def test_total_processed(self):
        """Kiểm tra tổng số bản ghi được xử lý"""
        self.assertEqual(len(self.dossiers), 8)
        self.assertEqual(self.summary["total_requests"], 8)

    def test_case_normal_qualified(self):
        """Case 1 & 2: Trường hợp thông thường - Đầy đủ, trong thẩm quyền"""
        d1 = self.dossier_map["YC-001"]
        self.assertEqual(d1["status"], STATUS_QUALIFIED)
        self.assertGreater(d1["pricing"]["final_proposed_price"], 0)
        self.assertFalse(d1["pricing"]["requires_manager_approval"])
        self.assertEqual(d1["approval_slip"], "") # Không cần phiếu duyệt
        self.assertIn("Kính gửi: Công ty TNHH Giải pháp FPT Smart", d1["draft_email"])

        d2 = self.dossier_map["YC-002"]
        self.assertEqual(d2["status"], STATUS_QUALIFIED)

    def test_case_missing_data(self):
        """Case 3 & 4: Trường hợp thiếu dữ liệu - Phải phát hiện và yêu cầu bổ sung"""
        d3 = self.dossier_map["YC-003"]
        self.assertEqual(d3["status"], STATUS_NEEDS_INFO)
        self.assertIn("Ngân sách dự kiến của khách hàng", d3["draft_email"])

        d4 = self.dossier_map["YC-004"]
        self.assertEqual(d4["status"], STATUS_NEEDS_INFO)
        self.assertIn("Thông tin liên hệ", d4["draft_email"])

    def test_case_infeasible(self):
        """Case 5 & 6: Không đáp ứng được - Hết kho hoặc không có mã SKU"""
        d5 = self.dossier_map["YC-005"] # Đòi 10 server HPE trong 3 ngày (kho có 3, cần 18 ngày)
        self.assertEqual(d5["status"], STATUS_INFEASIBLE)
        self.assertIn("Điều chỉnh thời hạn bàn giao", d5["draft_email"])

        d6 = self.dossier_map["YC-006"] # Máy in Canon không có trong Catalog
        self.assertEqual(d6["status"], STATUS_INFEASIBLE)

    def test_case_boundary_approval(self):
        """Case 7 & 8: Ranh giới quy tắc - Vượt thẩm quyền, chuyển Trưởng phòng duyệt"""
        d7 = self.dossier_map["YC-007"] # Đơn > 300 triệu và CK 8%
        self.assertEqual(d7["status"], STATUS_PENDING_APPROVAL)
        self.assertTrue(d7["pricing"]["requires_manager_approval"])
        self.assertNotEqual(d7["approval_slip"], "")
        self.assertIn("PHIẾU TRÌNH PHÊ DUYỆT CƠ HỘI BÁN HÀNG B2B", d7["approval_slip"])

        d8 = self.dossier_map["YC-008"] # Chiết khấu 10% (>5%)
        self.assertEqual(d8["status"], STATUS_PENDING_APPROVAL)
        self.assertIn("10.0% vượt thẩm quyền", d8["approval_slip"])

    def test_safety_guardrails(self):
        """Quy tắc an toàn: Không tự ý xác nhận bán hàng khi thiếu dữ kiện hoặc vượt quyền"""
        for d in self.dossiers:
            if d["status"] in [STATUS_NEEDS_INFO, STATUS_PENDING_APPROVAL, STATUS_INFEASIBLE]:
                # Không được xác nhận chốt đơn trong draft email
                self.assertNotIn("Minh An tiến hành giữ hàng và lập hợp đồng kinh tế", d["draft_email"])

    def test_financial_summary_separation(self):
        """Kiểm tra việc tính riêng rẽ tổng giá trị cơ hội Đủ điều kiện vs Chờ duyệt"""
        fin = self.summary["financials"]
        self.assertGreater(fin["total_value_qualified"], 0)
        self.assertGreater(fin["total_value_pending_approval"], 0)
        self.assertEqual(
            fin["total_active_pipeline_value"],
            fin["total_value_qualified"] + fin["total_value_pending_approval"]
        )

if __name__ == "__main__":
    unittest.main()

