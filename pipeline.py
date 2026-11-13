"""
Quy trình phối hợp tổng thể (End-to-End Orchestrator Pipeline)
Kết nối các Business Skills, Tool Calling, Rules Engine và Trace Logger
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from config import (
    STATUS_QUALIFIED, STATUS_NEEDS_INFO, STATUS_INFEASIBLE, STATUS_PENDING_APPROVAL
)
from trace_logger import AgentExecutionTrace, GlobalTraceRegistry
from agent_skills import (
    IntakeExtractionSkill,
    InventoryFeasibilitySkill,
    PricingPolicyEngineSkill,
    DocumentDraftingSkill
)

class SalesOpportunityPipeline:
    """Orchestrator điều phối toàn bộ chu trình xử lý cơ hội B2B của Minh An"""

    @classmethod
    def process_dataframe(cls, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        GlobalTraceRegistry.clear()
        dossiers: List[Dict[str, Any]] = []

        records = df.to_dict(orient="records")

        for idx, row in enumerate(records):
            req_id = str(row.get("request_id") or f"YC-{idx+1:03d}")
            cust_name = str(row.get("customer_name") or "")

            trace = AgentExecutionTrace(request_id=req_id, customer_name=cust_name)

            # --- BƯỚC 1: TIẾP NHẬN & PHÂN LOẠI THÔNG TIN ---
            intake_res = IntakeExtractionSkill.execute(row, trace)

            # --- BƯỚC 2: THẨM ĐỊNH TỒN KHO & SLA VẬN HÀNH ---
            # Ngay cả khi thiếu một vài thông tin, Agent vẫn tra cứu các sản phẩm đã nhận diện
            feasibility_res = InventoryFeasibilitySkill.execute(
                parsed_items=intake_res["parsed_items"],
                requested_deadline=intake_res["expected_deadline_days"],
                trace=trace
            )

            # --- BƯỚC 3: TÍNH GIÁ, CHIẾT KHẤU & QUY TẮC THẨM QUYỀN ---
            pricing_res = PricingPolicyEngineSkill.execute(
                evaluated_items=feasibility_res["evaluated_items"],
                budget=intake_res["budget"],
                requested_discount=intake_res["requested_discount_percent"],
                trace=trace
            )

            # --- BƯỚC 4: TỔNG HỢP HỒ SƠ, DỰ THẢO EMAIL & PHIẾU DUYỆT ---
            dossier = DocumentDraftingSkill.execute(
                intake_res=intake_res,
                feasibility_res=feasibility_res,
                pricing_res=pricing_res,
                rep_index=idx,
                trace=trace
            )

            # Đăng ký trace để lưu nhật ký truy vết
            GlobalTraceRegistry.register(trace)
            dossiers.append(dossier)

        # Tính toán bảng tổng hợp (Summary Statistics) theo yêu cầu đề thi Task 2
        summary_stats = cls._calculate_summary_statistics(dossiers)
        return dossiers, summary_stats

    @classmethod
    def _calculate_summary_statistics(cls, dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        count_qualified = sum(1 for d in dossiers if d["status"] == STATUS_QUALIFIED)
        count_needs_info = sum(1 for d in dossiers if d["status"] == STATUS_NEEDS_INFO)
        count_infeasible = sum(1 for d in dossiers if d["status"] == STATUS_INFEASIBLE)
        count_pending_approval = sum(1 for d in dossiers if d["status"] == STATUS_PENDING_APPROVAL)

        # Tính riêng tổng giá trị các cơ hội đủ điều kiện tiếp tục hoặc chờ duyệt
        total_value_qualified = sum(
            d["pricing"]["final_proposed_price"] for d in dossiers if d["status"] == STATUS_QUALIFIED
        )
        total_value_pending_approval = sum(
            d["pricing"]["final_proposed_price"] for d in dossiers if d["status"] == STATUS_PENDING_APPROVAL
        )
        total_pipeline_value = total_value_qualified + total_value_pending_approval

        return {
            "total_requests": len(dossiers),
            "counts": {
                STATUS_QUALIFIED: count_qualified,
                STATUS_NEEDS_INFO: count_needs_info,
                STATUS_INFEASIBLE: count_infeasible,
                STATUS_PENDING_APPROVAL: count_pending_approval,
            },
            "financials": {
                "total_value_qualified": total_value_qualified,
                "total_value_pending_approval": total_value_pending_approval,
                "total_active_pipeline_value": total_pipeline_value
            }
        }

