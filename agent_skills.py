"""
Bộ kỹ năng nghiệp vụ (Business Skills) của AI Agent Công ty Minh An
Phối hợp đồng bộ trong một quy trình xử lý khép kín:
- Skill 1: IntakeExtractionSkill (Bóc tách thực thể & Kiểm tra tính đầy đủ)
- Skill 2: InventoryFeasibilitySkill (Thẩm định tồn kho & SLA Vận hành)
- Skill 3: PricingPolicyEngineSkill (Áp giá niêm yết, chính sách chiết khấu & Thẩm quyền duyệt)
- Skill 4: DocumentDraftingSkill (Tạo Hồ sơ cơ hội, Dự thảo Email & Phiếu trình ký)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from config import (
    SALES_REPS, SALES_MANAGER, POLICY_RULES,
    STATUS_QUALIFIED, STATUS_NEEDS_INFO, STATUS_INFEASIBLE, STATUS_PENDING_APPROVAL
)
from knowledge_base import KnowledgeBase
from trace_logger import AgentExecutionTrace

class IntakeExtractionSkill:
    """Kỹ năng 1: Tiếp nhận, chuẩn hóa dữ liệu & Kiểm tra tính đầy đủ của thông tin"""

    @classmethod
    def execute(cls, raw_data: Dict[str, Any], trace: AgentExecutionTrace) -> Dict[str, Any]:
        req_id = raw_data.get("request_id") or raw_data.get("id") or "REQ-UNKNOWN"
        customer_name = str(raw_data.get("customer_name") or raw_data.get("khach_hang") or "").strip()
        contact_info = str(raw_data.get("contact_email") or raw_data.get("email") or raw_data.get("dien_thoai") or "").strip()
        budget_raw = raw_data.get("budget") or raw_data.get("ngan_sach") or 0
        deadline_raw = raw_data.get("expected_deadline_days") or raw_data.get("thoi_han_ngay") or 0
        discount_raw = raw_data.get("requested_discount_percent") or raw_data.get("chiet_khau_yeu_cau") or 0.0
        items_raw = raw_data.get("items_text") or raw_data.get("hang_muc") or raw_data.get("items") or ""
        notes = str(raw_data.get("notes") or raw_data.get("ghi_chu") or "").strip()

        # Chuẩn hóa ngân sách
        try:
            budget = float(str(budget_raw).replace(",", "").replace(".", "").replace("VNĐ", "").replace("VND", "").strip()) if budget_raw else 0.0
        except Exception:
            budget = 0.0

        # Chuẩn hóa deadline
        try:
            deadline = int(deadline_raw) if deadline_raw else 0
        except Exception:
            deadline = 0

        # Chuẩn hóa chiết khấu yêu cầu
        try:
            requested_discount = float(discount_raw) if discount_raw else 0.0
        except Exception:
            requested_discount = 0.0

        # Trích xuất danh sách sản phẩm / số lượng
        parsed_items = cls._parse_items(items_raw)

        # Kiểm tra tính đầy đủ (Completeness Validation)
        missing_fields = []
        if not customer_name:
            missing_fields.append("Tên khách hàng / doanh nghiệp")
        if not contact_info:
            missing_fields.append("Thông tin liên hệ (Email/Số điện thoại)")
        if not parsed_items:
            missing_fields.append("Hạng mục sản phẩm/dịch vụ cần mua")
        else:
            for itm in parsed_items:
                if itm["quantity"] <= 0:
                    missing_fields.append(f"Số lượng hợp lệ cho sản phẩm '{itm['raw_query']}'")
        if deadline <= 0:
            missing_fields.append("Thời hạn triển khai mong muốn (ngày)")
        if budget <= 0:
            missing_fields.append("Ngân sách dự kiến của khách hàng")

        is_complete = (len(missing_fields) == 0)

        # Log rule
        if not is_complete:
            trace.log_rule(
                rule_id="RULE_DATA_COMPLETENESS",
                rule_name="Kiểm tra tính đầy đủ thông tin đầu vào",
                condition=f"Thiếu các trường: {', '.join(missing_fields)}",
                action_taken="Gắn cờ yêu cầu làm rõ, kích hoạt quy trình soạn Email xin bổ sung thông tin.",
                is_exception=True
            )
        else:
            trace.log_rule(
                rule_id="RULE_DATA_COMPLETENESS",
                rule_name="Kiểm tra tính đầy đủ thông tin đầu vào",
                condition="Tất cả thông tin bắt buộc đã được cung cấp.",
                action_taken="Chuyển sang bước Tạo Hồ sơ Cơ hội & Gắn NVKD phụ trách.",
                is_exception=False
            )

        extracted_result = {
            "request_id": req_id,
            "customer_name": customer_name,
            "contact_info": contact_info,
            "budget": budget,
            "expected_deadline_days": deadline,
            "requested_discount_percent": requested_discount,
            "parsed_items": parsed_items,
            "notes": notes,
            "is_complete": is_complete,
            "missing_fields": missing_fields
        }

        trace.log_step(
            step_name="Phân loại & Kiểm tra thông tin",
            description="Bóc tách thực thể và thẩm định tính đầy đủ của yêu cầu khách hàng",
            inputs={"items_raw": str(items_raw), "budget": budget, "deadline": deadline},
            outputs={"parsed_items_count": len(parsed_items), "is_complete": is_complete, "missing_fields": missing_fields}
        )

        return extracted_result

    @classmethod
    def _parse_items(cls, items_raw: Any) -> List[Dict[str, Any]]:
        """Bóc tách text phi cấu trúc hoặc cấu trúc dạng '2x Dell R750; 5x Cisco C9200'"""
        if isinstance(items_raw, list):
            return items_raw

        items_str = str(items_raw).strip()
        if not items_str:
            return []

        parsed = []
        # Tách theo dấu chấm phẩy hoặc dấu phẩy hoặc xuống dòng
        lines = re.split(r"[;\n\r]+", items_str)
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Mẫu: "2x Dell R750" hoặc "Dell R750 (SL: 2)" hoặc "3 Máy chủ Dell" hoặc "Dell R750, sl 2"
            qty = 1
            query = line

            # Regex tìm số lượng dạng "3x" hoặc "3 x"
            m1 = re.match(r"^(\d+)\s*(?:x|\*)\s*(.+)$", line, re.IGNORECASE)
            if m1:
                qty = int(m1.group(1))
                query = m1.group(2).strip()
            else:
                # Regex tìm dạng "Tên sản phẩm - SL: 2" hoặc "...: 2"
                m2 = re.search(r"^(.*?)(?:[:\-,\(]\s*(?:sl|số lượng|qty)?\s*[:\s]*(\d+)\s*\)?)$", line, re.IGNORECASE)
                if m2:
                    query = m2.group(1).strip()
                    qty = int(m2.group(2))
                else:
                    # Regex tìm số đầu dòng: "2 Dell R750"
                    m3 = re.match(r"^(\d+)\s+(.+)$", line)
                    if m3:
                        qty = int(m3.group(1))
                        query = m3.group(2).strip()

            parsed.append({
                "raw_query": query,
                "quantity": qty
            })

        return parsed


class InventoryFeasibilitySkill:
    """Kỹ năng 2: Thẩm định khả năng đáp ứng Tồn kho & SLA Thời gian triển khai"""

    @classmethod
    def execute(cls, parsed_items: List[Dict[str, Any]], requested_deadline: int, trace: AgentExecutionTrace) -> Dict[str, Any]:
        evaluated_items = []
        all_in_stock = True
        all_lead_time_feasible = True
        max_required_lead_time = 0
        unknown_skus = []

        for item in parsed_items:
            q_name = item["raw_query"]
            qty = item["quantity"]

            # Tool Call 1: Tra cứu sản phẩm trong Catalog
            matched_prod = KnowledgeBase.find_product_by_query(q_name)
            trace.log_tool_call(
                tool_name="KnowledgeBase.find_product_by_query",
                arguments={"query_text": q_name},
                result=matched_prod["sku"] if matched_prod else "NOT_FOUND"
            )

            if not matched_prod:
                unknown_skus.append(q_name)
                all_in_stock = False
                all_lead_time_feasible = False
                evaluated_items.append({
                    "raw_query": q_name,
                    "sku": "UNKNOWN",
                    "product_name": f"Không tìm thấy mã khớp cho '{q_name}'",
                    "unit": "Cái",
                    "list_price": 0,
                    "requested_qty": qty,
                    "available_stock": 0,
                    "is_stock_available": False,
                    "min_lead_time_days": 30,
                    "lead_time_feasible": False,
                    "subtotal": 0,
                    "notes": "Chưa có trong Catalog chuẩn Minh An"
                })
                continue

            sku = matched_prod["sku"]
            list_price = matched_prod["list_price"]

            # Tool Call 2: Tra cứu Vận hành (Tồn kho & Lead time)
            inv_check = KnowledgeBase.check_inventory_and_sla(sku, qty, requested_deadline)
            trace.log_tool_call(
                tool_name="KnowledgeBase.check_inventory_and_sla",
                arguments={"sku": sku, "requested_qty": qty, "requested_days": requested_deadline},
                result=inv_check
            )

            if not inv_check["is_stock_available"]:
                all_in_stock = False
            if not inv_check["lead_time_feasible"]:
                all_lead_time_feasible = False

            if inv_check["min_lead_time_days"] > max_required_lead_time:
                max_required_lead_time = inv_check["min_lead_time_days"]

            subtotal = qty * list_price
            evaluated_items.append({
                "raw_query": q_name,
                "sku": sku,
                "product_name": matched_prod["name"],
                "unit": matched_prod["unit"],
                "list_price": list_price,
                "requested_qty": qty,
                "available_stock": inv_check["available_stock"],
                "is_stock_available": inv_check["is_stock_available"],
                "min_lead_time_days": inv_check["min_lead_time_days"],
                "lead_time_feasible": inv_check["lead_time_feasible"],
                "subtotal": subtotal,
                "notes": inv_check["details"]
            })

        # Log rule
        if unknown_skus:
            trace.log_rule(
                rule_id="RULE_PRODUCT_IDENTIFICATION",
                rule_name="Nhận diện sản phẩm trong Danh mục",
                condition=f"Phát hiện sản phẩm lạ: {unknown_skus}",
                action_taken="Cảnh báo NVKD kiểm tra bảng giá ngoại bộ hoặc làm rõ mã thiết bị với khách hàng.",
                is_exception=True
            )

        if not all_lead_time_feasible:
            trace.log_rule(
                rule_id="RULE_SLA_LEAD_TIME",
                rule_name="Kiểm tra cam kết thời hạn giao hàng (SLA)",
                condition=f"Thời hạn khách yêu cầu ({requested_deadline} ngày) < Thời gian Vận hành cần ({max_required_lead_time} ngày).",
                action_taken="Chặn cam kết thời hạn sai; đề xuất lùi ngày giao hoặc xin duyệt khẩn cấp.",
                is_exception=True
            )

        feasibility_result = {
            "evaluated_items": evaluated_items,
            "all_in_stock": all_in_stock,
            "all_lead_time_feasible": all_lead_time_feasible,
            "max_required_lead_time": max_required_lead_time,
            "unknown_skus": unknown_skus,
            "is_operationally_feasible": (len(unknown_skus) == 0 and all_lead_time_feasible)
        }

        trace.log_step(
            step_name="Thẩm định tồn kho & giá",
            description="Kiểm tra khả dụng kho thực tế và khả năng cam kết thời hạn với Vận hành",
            inputs={"items_count": len(parsed_items), "requested_deadline": requested_deadline},
            outputs={
                "all_in_stock": all_in_stock,
                "lead_time_feasible": all_lead_time_feasible,
                "max_lead_time": max_required_lead_time
            }
        )

        return feasibility_result


class PricingPolicyEngineSkill:
    """Kỹ năng 3: Tính toán Báo giá, Chính sách Chiết khấu & Kiểm tra Thẩm quyền Phê duyệt"""

    @classmethod
    def execute(
        cls,
        evaluated_items: List[Dict[str, Any]],
        budget: float,
        requested_discount: float,
        trace: AgentExecutionTrace
    ) -> Dict[str, Any]:
        # 1. Tính tổng giá trị niêm yết (List Price Subtotal)
        total_list_price = sum(item["subtotal"] for item in evaluated_items)

        # 2. Xác định chiết khấu tiêu chuẩn theo bậc thang doanh số
        standard_discount = 0.0
        for tier in POLICY_RULES["DISCOUNT_TIERS"]:
            if tier["min_value"] <= total_list_price < tier["max_value"]:
                standard_discount = tier["standard_discount"]
                break

        # 3. Quyết định tỷ lệ chiết khấu đề xuất
        # Nếu khách có yêu cầu chiết khấu riêng:
        applied_discount_percent = requested_discount if requested_discount > 0 else standard_discount
        discount_amount = total_list_price * (applied_discount_percent / 100.0)
        final_proposed_price = total_list_price - discount_amount

        # 4. Kiểm tra các ranh giới quy tắc thẩm quyền (Authority Checks)
        approval_reasons = []

        # Ranh giới 1: Chiết khấu vượt thẩm quyền NVKD (quá 5% hoặc vượt chuẩn)
        if applied_discount_percent > POLICY_RULES["MAX_REP_DISCOUNT_PERCENT"]:
            approval_reasons.append(
                f"Mức chiết khấu {applied_discount_percent}% vượt thẩm quyền tối đa của NVKD ({POLICY_RULES['MAX_REP_DISCOUNT_PERCENT']}%)."
            )
            trace.log_rule(
                rule_id="RULE_DISCOUNT_AUTHORITY",
                rule_name="Thẩm quyền chiết khấu NVKD",
                condition=f"Chiết khấu {applied_discount_percent}% > {POLICY_RULES['MAX_REP_DISCOUNT_PERCENT']}%",
                action_taken="Chuyển Trưởng phòng Kinh doanh phê duyệt ngoại lệ chiết khấu đặc biệt.",
                is_exception=True
            )

        # Ranh giới 2: Giá trị đơn hàng vượt hạn mức 300 triệu
        if final_proposed_price > POLICY_RULES["MAX_REP_DEAL_VALUE"]:
            approval_reasons.append(
                f"Tổng giá trị đơn hàng ({final_proposed_price:,.0f} VNĐ) vượt thẩm quyền tối đa của NVKD ({POLICY_RULES['MAX_REP_DEAL_VALUE']:,.0f} VNĐ)."
            )
            trace.log_rule(
                rule_id="RULE_DEAL_VALUE_AUTHORITY",
                rule_name="Hạn mức giá trị cơ hội của NVKD",
                condition=f"Giá trị đề xuất {final_proposed_price:,.0f} > {POLICY_RULES['MAX_REP_DEAL_VALUE']:,.0f}",
                action_taken="Chuyển Trưởng phòng Kinh doanh phê duyệt hạn mức giá trị lớn.",
                is_exception=True
            )

        # Ranh giới 3: So khớp ngân sách khách hàng
        budget_gap = 0.0
        is_budget_exceeded = False
        if budget > 0 and final_proposed_price > budget:
            budget_gap = final_proposed_price - budget
            is_budget_exceeded = True
            approval_reasons.append(
                f"Giá đề xuất ({final_proposed_price:,.0f} VNĐ) vượt ngân sách khách dự kiến ({budget:,.0f} VNĐ, chênh lệch {budget_gap:,.0f} VNĐ)."
            )
            trace.log_rule(
                rule_id="RULE_BUDGET_COMPARISON",
                rule_name="Đối chiếu Ngân sách khách hàng",
                condition=f"Giá đề xuất ({final_proposed_price:,.0f}) > Ngân sách ({budget:,.0f})",
                action_taken="Ghi nhận rủi ro ngân sách, chuyển Trưởng phòng quyết định giảm margin hoặc tư vấn phương án cắt giảm hạng mục.",
                is_exception=True
            )

        requires_manager_approval = (len(approval_reasons) > 0)

        pricing_result = {
            "total_list_price": total_list_price,
            "standard_discount_percent": standard_discount,
            "applied_discount_percent": applied_discount_percent,
            "discount_amount": discount_amount,
            "final_proposed_price": final_proposed_price,
            "budget": budget,
            "budget_gap": budget_gap,
            "is_budget_exceeded": is_budget_exceeded,
            "requires_manager_approval": requires_manager_approval,
            "approval_reasons": approval_reasons
        }

        trace.log_step(
            step_name="Lập Báo giá & Dự thảo đề xuất",
            description="Áp bảng giá niêm yết mới nhất, chính sách chiết khấu và kiểm tra thẩm quyền",
            inputs={"total_list_price": total_list_price, "requested_discount": requested_discount, "budget": budget},
            outputs={
                "final_proposed_price": final_proposed_price,
                "requires_approval": requires_manager_approval,
                "reasons": approval_reasons
            }
        )

        return pricing_result


class DocumentDraftingSkill:
    """Kỹ năng 4: Tự động tạo Hồ sơ Cơ hội, Dự thảo Email phản hồi và Phiếu chuyển duyệt"""

    @classmethod
    def execute(
        cls,
        intake_res: Dict[str, Any],
        feasibility_res: Dict[str, Any],
        pricing_res: Dict[str, Any],
        rep_index: int,
        trace: AgentExecutionTrace
    ) -> Dict[str, Any]:
        # Gán NVKD phụ trách theo cơ chế phân bổ
        assigned_rep = SALES_REPS[rep_index % len(SALES_REPS)]
        approver = SALES_MANAGER

        # Quyết định trạng thái cuối cùng (Final Status Decision)
        if not intake_res["is_complete"]:
            status = STATUS_NEEDS_INFO
            next_step = f"NVKD {assigned_rep['name']} gửi email yêu cầu khách hàng bổ sung: {', '.join(intake_res['missing_fields'])}."
        elif not feasibility_res["is_operationally_feasible"]:
            status = STATUS_INFEASIBLE
            reasons = []
            if feasibility_res["unknown_skus"]:
                reasons.append(f"Không có mã sản phẩm: {', '.join(feasibility_res['unknown_skus'])}")
            if not feasibility_res["all_lead_time_feasible"]:
                reasons.append(f"Thời gian giao tối thiểu ({feasibility_res['max_required_lead_time']} ngày) không đáp ứng deadline khách ({intake_res['expected_deadline_days']} ngày)")
            next_step = f"NVKD liên hệ khách đàm phán kéo dài thời gian giao hoặc tư vấn đổi mã tương đương."
        elif pricing_res["requires_manager_approval"]:
            status = STATUS_PENDING_APPROVAL
            next_step = f"Chuyển Phiếu trình ký tới Trưởng phòng {approver['name']} phê duyệt ({', '.join(pricing_res['approval_reasons'])})."
        else:
            status = STATUS_QUALIFIED
            next_step = f"NVKD {assigned_rep['name']} gửi Báo giá chính thức và xúc tiến ký kết hợp đồng."

        trace.complete(final_status=status)

        # 1. Soạn Dự thảo Email phản hồi khách hàng (Customer Draft Email)
        draft_email = cls._draft_customer_email(
            status=status,
            customer_name=intake_res["customer_name"],
            rep=assigned_rep,
            intake_res=intake_res,
            feasibility_res=feasibility_res,
            pricing_res=pricing_res
        )

        # 2. Soạn Phiếu chuyển duyệt Trưởng phòng (nếu cần)
        approval_slip = ""
        if status == STATUS_PENDING_APPROVAL or pricing_res["requires_manager_approval"]:
            approval_slip = cls._draft_approval_slip(
                intake_res=intake_res,
                feasibility_res=feasibility_res,
                pricing_res=pricing_res,
                rep=assigned_rep,
                approver=approver
            )

        # 3. Tạo Hồ sơ Cơ hội (Dossier)
        dossier = {
            "opportunity_id": f"OPP-{intake_res['request_id']}",
            "request_id": intake_res["request_id"],
            "status": status,
            "customer_name": intake_res["customer_name"],
            "contact_info": intake_res["contact_info"],
            "assigned_rep": assigned_rep,
            "approver": approver if status == STATUS_PENDING_APPROVAL else None,
            "created_date": trace.start_time.strftime("%d/%m/%Y %H:%M"),
            "items_table": feasibility_res["evaluated_items"],
            "pricing": pricing_res,
            "lead_time_days": feasibility_res["max_required_lead_time"],
            "next_action": next_step,
            "draft_email": draft_email,
            "approval_slip": approval_slip,
            "trace_id": intake_res["request_id"]
        }

        trace.log_step(
            step_name="Kết thúc: Cập nhật & Theo dõi",
            description="Tạo Hồ sơ cơ hội, xuất bản nháp email phản hồi và phiếu chuyển duyệt",
            inputs={"status": status},
            outputs={"opportunity_id": dossier["opportunity_id"], "status": status, "assigned_rep": assigned_rep["name"]}
        )

        return dossier

    @classmethod
    def _draft_customer_email(
        cls,
        status: str,
        customer_name: str,
        rep: Dict[str, str],
        intake_res: Dict[str, Any],
        feasibility_res: Dict[str, Any],
        pricing_res: Dict[str, Any]
    ) -> str:
        cust = customer_name or "Quý Khách hàng"
        rep_name = rep["name"]
        rep_mail = rep["email"]

        if status == STATUS_NEEDS_INFO:
            missing_text = "\n".join([f"  - {f}" for f in intake_res["missing_fields"]])
            return f"""Kính gửi: {cust},

Công ty Cổ phần Công nghệ Minh An xin trân trọng cảm ơn Quý công ty đã quan tâm và gửi yêu cầu hợp tác về thiết bị và giải pháp công nghệ.

Để bộ phận kỹ thuật và kinh doanh của chúng tôi có thể lập bảng báo giá chính xác cùng phương án triển khai tối ưu nhất, kính mong Quý khách vui lòng làm rõ/bổ sung một số thông tin còn thiếu sau:
{missing_text}

Quý khách có thể phản hồi trực tiếp qua email này hoặc liên hệ hotline để được hỗ trợ nhanh nhất. Chúng tôi sẽ tiến hành thẩm định và phản hồi bản báo giá hoàn chỉnh ngay khi nhận được thông tin.

Trân trọng cảm ơn sự hợp tác của Quý công ty!

--
{rep_name} | Bộ phận Kinh doanh Doanh nghiệp
Công ty Cổ phần Công nghệ Minh An
Email: {rep_mail} | Hotline: 1900 6868
"""

        elif status == STATUS_INFEASIBLE:
            return f"""Kính gửi: {cust},

Công ty Công nghệ Minh An xin cảm ơn Quý khách đã gửi yêu cầu chào giá.

Sau khi đối chiếu với tồn kho khả dụng và năng lực cung ứng của Bộ phận Vận hành, chúng tôi xin phép thông báo tình trạng đáp ứng cho đơn hàng như sau:
- Thời hạn Quý khách mong muốn: {intake_res['expected_deadline_days']} ngày.
- Thời gian tối thiểu hoàn tất chuẩn bị & kiểm thử kỹ thuật: {feasibility_res['max_required_lead_time']} ngày làm việc (do cần điều phối nhập hàng và cấu hình tiêu chuẩn).

Để không làm gián đoạn kế hoạch của Quý khách, Minh An xin đề xuất hai phương án:
1. Điều chỉnh thời hạn bàn giao sang {feasibility_res['max_required_lead_time']} ngày làm việc.
2. Thay thế bằng các mã thiết bị tương đương có sẵn trong kho ngay hôm nay (chuyên viên kinh doanh sẽ gọi trao đổi trực tiếp).

Chuyên viên phụ trách {rep_name} sẽ liên hệ Quý công ty trong vòng 2 giờ tới để cùng thống nhất giải pháp tối ưu.

Trân trọng!

--
{rep_name} | Bộ phận Kinh doanh Doanh nghiệp
Công ty Cổ phần Công nghệ Minh An
Email: {rep_mail}
"""

        elif status == STATUS_PENDING_APPROVAL:
            return f"""Kính gửi: {cust},

Công ty Cổ phần Công nghệ Minh An trân trọng cảm ơn Quý công ty đã tín nhiệm và gửi đề xuất đặt hàng thiết bị công nghệ.

Hồ sơ yêu cầu của Quý khách với tổng giá trị niêm yết {pricing_res['total_list_price']:,.0f} VNĐ và đề xuất chính sách chiết khấu {pricing_res['applied_discount_percent']}% đã được ghi nhận. 
Do đơn vị có quy mô lớn và chính sách ưu đãi đặc biệt vượt thẩm quyền tiêu chuẩn, hiện tại hồ sơ đang được trình Trưởng phòng Kinh doanh và Ban Giám đốc xem xét duyệt hạn mức chiết khấu tối đa cùng thời hạn giao hàng cam kết tốt nhất cho Quý khách.

Bản Báo giá chính thức kèm phê duyệt đặc biệt sẽ được gửi tới Quý khách trước 17h00 hôm nay.

Rất mong được đồng hành lâu dài cùng Quý công ty!

--
{rep_name} | Bộ phận Kinh doanh Doanh nghiệp
Công ty Cổ phần Công nghệ Minh An
Email: {rep_mail}
"""

        else: # STATUS_QUALIFIED
            items_str = "\n".join([
                f"  + {it['product_name']} ({it['sku']}): SL {it['requested_qty']} {it['unit']} x {it['list_price']:,.0f} đ = {it['subtotal']:,.0f} VNĐ"
                for it in feasibility_res["evaluated_items"]
            ])
            return f"""Kính gửi: {cust},

Công ty Cổ phần Công nghệ Minh An trân trọng gửi tới Quý công ty phương án báo giá và tiến độ triển khai cho yêu cầu mã {intake_res['request_id']}:

1. DANH MỤC THIẾT BỊ & DỊCH VỤ:
{items_str}

2. TỔNG HỢP GIÁ TRỊ ĐỀ XUẤT:
- Tổng giá niêm yết: {pricing_res['total_list_price']:,.0f} VNĐ
- Chiết khấu áp dụng ({pricing_res['applied_discount_percent']}%): -{pricing_res['discount_amount']:,.0f} VNĐ
- TỔNG GIÁ TRỊ THANH TOÁN (Chưa VAT): {pricing_res['final_proposed_price']:,.0f} VNĐ

3. CAM KẾT VẬN HÀNH & BẢO HÀNH:
- Tình trạng hàng: Có sẵn 100% trong kho khả dụng.
- Thời gian giao hàng & bàn giao: {feasibility_res['max_required_lead_time']} ngày làm việc kể từ ngày xác nhận đặt hàng.
- Bảo hành chính hãng theo tiêu chuẩn nhà sản xuất tại chỗ.

Báo giá có hiệu lực trong vòng 15 ngày làm việc. Quý khách vui lòng ký xác nhận phản hồi để Minh An tiến hành giữ hàng và lập hợp đồng kinh tế.

Trân trọng cảm ơn Quý khách!

--
{rep_name} | Chuyên viên Kinh doanh B2B
Công ty Cổ phần Công nghệ Minh An
Email: {rep_mail}
"""

    @classmethod
    def _draft_approval_slip(
        cls,
        intake_res: Dict[str, Any],
        feasibility_res: Dict[str, Any],
        pricing_res: Dict[str, Any],
        rep: Dict[str, str],
        approver: Dict[str, str]
    ) -> str:
        reasons_bullet = "\n".join([f"  * {r}" for r in pricing_res["approval_reasons"]])
        items_summary = ", ".join([f"{it['requested_qty']}x {it['sku']}" for it in feasibility_res["evaluated_items"]])

        return f"""================================================================================
                    PHIẾU TRÌNH PHÊ DUYỆT CƠ HỘI BÁN HÀNG B2B
                     (Dành cho các trường hợp vượt thẩm quyền NVKD)
================================================================================
Kính gửi: {approver['name']}
Người lập phiếu: {rep['name']} ({rep['id']}) - Bộ phận Kinh doanh
Ngày lập: {trace_logger_now()}

1. THÔNG TIN KHÁCH HÀNG & CƠ HỘI:
- Khách hàng: {intake_res['customer_name']} (Liên hệ: {intake_res['contact_info']})
- Mã yêu cầu: {intake_res['request_id']} | Hạng mục: {items_summary}
- Thời hạn khách yêu cầu: {intake_res['expected_deadline_days']} ngày | Lead-time kỹ thuật: {feasibility_res['max_required_lead_time']} ngày

2. CHỈ SỐ TÀI CHÍNH & ĐỀ XUẤT GIÁ:
- Tổng giá trị niêm yết: {pricing_res['total_list_price']:,.0f} VNĐ
- Ngân sách khách hàng khai báo: {pricing_res['budget']:,.0f} VNĐ
- Chiết khấu tiêu chuẩn chính sách: {pricing_res['standard_discount_percent']}%
- Chiết khấu khách yêu cầu / NVKD đề xuất: {pricing_res['applied_discount_percent']}%
- Tổng giá trị đề xuất sau chiết khấu: {pricing_res['final_proposed_price']:,.0f} VNĐ

3. CĂN CỨ VƯỢT THẨM QUYỀN CẦN TRƯỞNG PHÒNG DUYỆT:
{reasons_bullet}

4. ĐỀ XUẤT CỦA NVKD PHỤ TRÁCH:
Kính đề nghị Trưởng phòng phê duyệt chính sách chiết khấu {pricing_res['applied_discount_percent']}% để chốt thương vụ lớn, tạo tiền đề mở rộng cung cấp dịch vụ bảo trì định kỳ cho khách hàng trong các quý tiếp theo.

Ý KIẾN PHÊ DUYỆT CỦA TRƯỞNG PHÒNG:
[  ] ĐỒNG Ý PHÊ DUYỆT      [  ] TỪ CHỐI      [  ] YÊU CẦU ĐÀM PHÁN LẠI
Chữ ký: .......................................
================================================================================
"""

def trace_logger_now():
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M")

