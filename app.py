"""
ỨNG DỤNG AI AGENT XỬ LÝ CƠ HỘI BÁN HÀNG B2B - CÔNG TY MINH AN
Học phần: AI301 AI Agent - Đề dự án 01
Giao diện trực quan tích hợp nạp dữ liệu (CSV, XLSX, Google Sheets),
phân tích tự động đa kỹ năng, hiển thị Hồ sơ cơ hội, Báo giá, Dự thảo Email,
Phiếu chuyển duyệt và Nhật ký truy vết (Trace logs) minh bạch.
"""

import streamlit as st
import pandas as pd
import json
from config import (
    SALES_REPS, SALES_MANAGER, POLICY_RULES,
    STATUS_QUALIFIED, STATUS_NEEDS_INFO, STATUS_INFEASIBLE, STATUS_PENDING_APPROVAL
)
from knowledge_base import KnowledgeBase
from trace_logger import GlobalTraceRegistry
from data_loader import (
    load_from_csv, load_from_excel, load_from_google_sheets,
    get_default_sample_dataframe
)
from pipeline import SalesOpportunityPipeline

st.set_page_config(
    page_title="AI Agent B2B - Minh An Company",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện doanh nghiệp chuyên nghiệp
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0d3b66 0%, #0077b6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #0077b6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-qualified { background-color: #d1e7dd; color: #0f5132; }
    .status-needs-info { background-color: #fff3cd; color: #664d03; }
    .status-infeasible { background-color: #f8d7da; color: #842029; }
    .status-pending { background-color: #cfe2ff; color: #084298; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "df_input" not in st.session_state:
    st.session_state.df_input = get_default_sample_dataframe()
    st.session_state.data_source_name = "Bộ dữ liệu kiểm thử chuẩn (Built-in 8 Cases)"
if "dossiers" not in st.session_state or "summary_stats" not in st.session_state:
    dossiers, summary = SalesOpportunityPipeline.process_dataframe(st.session_state.df_input)
    st.session_state.dossiers = dossiers
    st.session_state.summary_stats = summary

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("Bộ điều khiển Agent")
    st.caption("AI301 | Đề án 01 - Xử lý cơ hội B2B")

    st.markdown("---")
    st.subheader("📥 Nạp Dữ liệu Đầu vào")
    input_mode = st.radio(
        "Chọn nguồn dữ liệu:",
        ["Bộ dữ liệu mẫu đề thi (8 Cases)", "Tải lên File (Excel / CSV)", "Dán link Google Sheets"],
        index=0
    )

    if input_mode == "Bộ dữ liệu mẫu đề thi (8 Cases)":
        if st.button("🔄 Nạp lại Dữ liệu Mẫu", use_container_width=True):
            st.session_state.df_input = get_default_sample_dataframe()
            st.session_state.data_source_name = "Bộ dữ liệu kiểm thử chuẩn (Built-in 8 Cases)"
            dossiers, summary = SalesOpportunityPipeline.process_dataframe(st.session_state.df_input)
            st.session_state.dossiers = dossiers
            st.session_state.summary_stats = summary
            st.success("Đã nạp và xử lý bộ dữ liệu mẫu!")

    elif input_mode == "Tải lên File (Excel / CSV)":
        uploaded_file = st.file_uploader("Chọn file .xlsx hoặc .csv", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                df_loaded, msg = load_from_csv(uploaded_file)
            else:
                df_loaded, msg = load_from_excel(uploaded_file)

            if df_loaded is not None:
                st.success(msg)
                if st.button("🚀 Xử lý Tập dữ liệu Mới", type="primary", use_container_width=True):
                    st.session_state.df_input = df_loaded
                    st.session_state.data_source_name = f"File: {uploaded_file.name}"
                    dossiers, summary = SalesOpportunityPipeline.process_dataframe(df_loaded)
                    st.session_state.dossiers = dossiers
                    st.session_state.summary_stats = summary
                    st.rerun()
            else:
                st.error(msg)

    elif input_mode == "Dán link Google Sheets":
        st.markdown("**Hướng dẫn:** Google Sheet cần bật quyền *'Bất kỳ ai có đường liên kết đều có thể xem'*.")
        gsheet_url = st.text_input(
            "Link Google Sheets:",
            placeholder="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        )
        if st.button("📥 Tải & Phân tích từ Google Sheet", type="primary", use_container_width=True):
            if gsheet_url:
                with st.spinner("Đang tải dữ liệu từ Google Sheets..."):
                    df_loaded, msg = load_from_google_sheets(gsheet_url)
                    if df_loaded is not None:
                        st.success(msg)
                        st.session_state.df_input = df_loaded
                        st.session_state.data_source_name = "Google Sheets"
                        dossiers, summary = SalesOpportunityPipeline.process_dataframe(df_loaded)
                        st.session_state.dossiers = dossiers
                        st.session_state.summary_stats = summary
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Vui lòng nhập đường link Google Sheet hợp lệ.")

    st.markdown("---")
    st.subheader("⚙️ Quy tắc & Thẩm quyền")
    st.markdown(f"""
    - **NVKD tự quyết:** Đơn ≤ **{POLICY_RULES['MAX_REP_DEAL_VALUE']:,.0f} VNĐ**
    - **Chiết khấu tối đa NVKD:** ≤ **{POLICY_RULES['MAX_REP_DISCOUNT_PERCENT']}%**
    - **Vượt thẩm quyền:** Trình Trưởng phòng KD (*{SALES_MANAGER['name']}*)
    - **Đội ngũ:** 6 NVKD điều phối tự động
    """)

    st.markdown("---")
    st.caption("🛡️ Minh An AI Agent v2.5 | Auto-Trace Enabled")

# ----------------- MAIN HEADER -----------------
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 1.9rem; font-weight:700;">HỆ THỐNG AI AGENT XỬ LÝ CƠ HỘI BÁN HÀNG B2B</h1>
    <p style="margin:6px 0 0 0; opacity:0.95; font-size:1.05rem;">
        Doanh nghiệp: <b>Công ty Cổ phần Công nghệ Minh An</b> | Đề án: <b>AI301 AI AGENT - Đề 01</b>
    </p>
    <p style="margin:4px 0 0 0; font-size:0.85rem; opacity:0.8;">
        Nguồn dữ liệu hiện tại: <i>{}</i> ({:,} yêu cầu được xử lý)
    </p>
</div>
""".format(st.session_state.data_source_name, len(st.session_state.dossiers)), unsafe_allow_html=True)

# ----------------- TABS -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard & Tổng hợp",
    "📋 Hồ sơ Cơ hội & Đề xuất",
    "🔍 Nhật ký Truy vết Agent (Logs)",
    "🏢 Danh mục & Kho Vận hành",
    "📑 Thuyết minh Thiết kế (Task 1)"
])

# ================= TAB 1: DASHBOARD & TỔNG HỢP =================
with tab1:
    summary = st.session_state.summary_stats
    counts = summary["counts"]
    financials = summary["financials"]

    # 4 Metric Boxes theo 4 trạng thái
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div style="background:#e8f5e9; border-left:5px solid #2e7d32; padding:15px; border-radius:8px;">
            <div style="color:#2e7d32; font-size:0.85rem; font-weight:600;">CÓ THỂ TIẾP TỤC</div>
            <div style="font-size:2rem; font-weight:700; color:#1b5e20;">{counts[STATUS_QUALIFIED]}</div>
            <div style="font-size:0.75rem; color:#555;">Đủ dữ kiện, sẵn hàng, trong quyền</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:#fffde7; border-left:5px solid #f9a825; padding:15px; border-radius:8px;">
            <div style="color:#f57f17; font-size:0.85rem; font-weight:600;">CẦN BỔ SUNG THÔNG TIN</div>
            <div style="font-size:2rem; font-weight:700; color:#e65100;">{counts[STATUS_NEEDS_INFO]}</div>
            <div style="font-size:0.75rem; color:#555;">Thiếu ngân sách, SL, thời hạn...</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="background:#ffebee; border-left:5px solid #c62828; padding:15px; border-radius:8px;">
            <div style="color:#c62828; font-size:0.85rem; font-weight:600;">CHƯA ĐÁP ỨNG</div>
            <div style="font-size:2rem; font-weight:700; color:#b71c1c;">{counts[STATUS_INFEASIBLE]}</div>
            <div style="font-size:0.75rem; color:#555;">Hết hàng, lead time gấp, sai SKU</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div style="background:#e3f2fd; border-left:5px solid #1565c0; padding:15px; border-radius:8px;">
            <div style="color:#1565c0; font-size:0.85rem; font-weight:600;">CHỜ TRƯỞNG PHÒNG DUYỆT</div>
            <div style="font-size:2rem; font-weight:700; color:#0d47a1;">{counts[STATUS_PENDING_APPROVAL]}</div>
            <div style="font-size:0.75rem; color:#555;">>300tr, CK >5%, vượt ngân sách</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Chỉ số tài chính bắt buộc theo đề thi
    col_fin1, col_fin2, col_fin3 = st.columns(3)
    with col_fin1:
        st.metric(
            label="💰 Tổng Giá trị Đủ điều kiện tiếp tục",
            value=f"{financials['total_value_qualified']:,.0f} VNĐ",
            help="Tổng giá trị đề xuất của các cơ hội hợp lệ, sẵn hàng và trong quyền tự quyết của NVKD"
        )
    with col_fin2:
        st.metric(
            label="⚖️ Tổng Giá trị Chờ duyệt (Vượt quyền)",
            value=f"{financials['total_value_pending_approval']:,.0f} VNĐ",
            help="Tổng giá trị đề xuất của các cơ hội quy mô lớn hoặc chiết khấu đặc biệt đang chờ Trưởng phòng ký"
        )
    with col_fin3:
        st.metric(
            label="📈 Tổng Pipeline Tiềm năng (Đủ điều kiện + Chờ duyệt)",
            value=f"{financials['total_active_pipeline_value']:,.0f} VNĐ",
            help="Tổng giá trị cơ hội có khả năng chốt doanh thu"
        )

    st.markdown("---")
    st.subheader("📑 Bảng Tổng hợp Tình trạng Cơ hội Bán hàng")

    # Tạo bảng hiển thị tổng quan
    table_rows = []
    for d in st.session_state.dossiers:
        p = d["pricing"]
        table_rows.append({
            "Mã Cơ hội": d["opportunity_id"],
            "Khách hàng": d["customer_name"],
            "Trạng thái": d["status"],
            "NVKD Phụ trách": d["assigned_rep"]["name"],
            "Tổng giá niêm yết (VNĐ)": f"{p['total_list_price']:,.0f}",
            "Chiết khấu (%)": f"{p['applied_discount_percent']}%",
            "Giá đề xuất sau CK (VNĐ)": f"{p['final_proposed_price']:,.0f}",
            "Ngân sách khách": f"{p['budget']:,.0f} VNĐ" if p['budget'] > 0 else "Chưa rõ",
            "Thời hạn (ngày)": d["lead_time_days"],
            "Bước xử lý tiếp theo": d["next_action"]
        })
    df_summary_table = pd.DataFrame(table_rows)

    def highlight_status(val):
        if val == STATUS_QUALIFIED:
            return "background-color: #d1e7dd; color: #0f5132; font-weight: bold;"
        elif val == STATUS_NEEDS_INFO:
            return "background-color: #fff3cd; color: #664d03; font-weight: bold;"
        elif val == STATUS_INFEASIBLE:
            return "background-color: #f8d7da; color: #842029; font-weight: bold;"
        elif val == STATUS_PENDING_APPROVAL:
            return "background-color: #cfe2ff; color: #084298; font-weight: bold;"
        return ""

    st.dataframe(
        df_summary_table.style.map(highlight_status, subset=["Trạng thái"]),
        use_container_width=True,
        hide_index=True
    )

    # Tải file kết quả
    col_dl1, col_dl2 = st.columns([1, 4])
    with col_dl1:
        csv_export = df_summary_table.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Tải Báo cáo Tổng hợp (CSV)",
            data=csv_export,
            file_name="Bao_cao_tong_hop_co_hoi_MinhAn.csv",
            mime="text/csv",
            use_container_width=True
        )


# ================= TAB 2: HỒ SƠ CƠ HỘI & ĐỀ XUẤT =================
with tab2:
    st.subheader("🔍 Chi tiết Hồ sơ Cơ hội & Đề xuất Kinh doanh")

    opp_options = [f"{d['opportunity_id']} - {d['customer_name']} [{d['status']}]" for d in st.session_state.dossiers]
    selected_idx = st.selectbox("Chọn cơ hội để xem Hồ sơ chi tiết:", range(len(opp_options)), format_func=lambda i: opp_options[i])

    curr_dossier = st.session_state.dossiers[selected_idx]
    p = curr_dossier["pricing"]

    # Header Card của Hồ sơ
    st.markdown(f"""
    <div style="background:#f8f9fa; border:1px solid #dee2e6; border-radius:10px; padding:18px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0; color:#0d3b66;">{curr_dossier['opportunity_id']}: {curr_dossier['customer_name']}</h3>
            <span class="status-badge" style="background-color: {'#d1e7dd' if curr_dossier['status']==STATUS_QUALIFIED else '#fff3cd' if curr_dossier['status']==STATUS_NEEDS_INFO else '#f8d7da' if curr_dossier['status']==STATUS_INFEASIBLE else '#cfe2ff'};">
                {curr_dossier['status']}
            </span>
        </div>
        <p style="margin:6px 0 0 0; color:#6c757d; font-size:0.9rem;">
            <b>Liên hệ:</b> {curr_dossier['contact_info'] or 'Chưa có thông tin'} | 
            <b>NVKD phụ trách:</b> {curr_dossier['assigned_rep']['name']} ({curr_dossier['assigned_rep']['email']}) | 
            <b>Ngày tạo:</b> {curr_dossier['created_date']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Bảng chi tiết hạng mục thẩm định
    st.markdown("#### 1. Bảng Đối chiếu Hạng mục & Khả năng Đáp ứng Kho")
    items_data = []
    for it in curr_dossier["items_table"]:
        items_data.append({
            "Mã SKU": it["sku"],
            "Tên Hạng mục": it["product_name"],
            "ĐVT": it["unit"],
            "SL Yêu cầu": it["requested_qty"],
            "Tồn kho Khả dụng": it["available_stock"],
            "Đủ hàng kho?": "✅ Có sẵn" if it["is_stock_available"] else "❌ Thiếu kho",
            "Đơn giá Niêm yết": f"{it['list_price']:,.0f} VNĐ",
            "Lead-time giao (ngày)": it["min_lead_time_days"],
            "Thành tiền (VNĐ)": f"{it['subtotal']:,.0f}"
        })
    df_items = pd.DataFrame(items_data)
    st.dataframe(df_items, use_container_width=True, hide_index=True)

    # Thống kê tài chính & Bước tiếp theo
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### 2. Phân tích Giá trị & Chiết khấu")
        st.write(f"- **Tổng giá niêm yết:** `{p['total_list_price']:,.0f} VNĐ`")
        st.write(f"- **Chính sách chiết khấu chuẩn:** `{p['standard_discount_percent']}%`")
        st.write(f"- **Chiết khấu áp dụng đề xuất:** `{p['applied_discount_percent']}%` (Giảm `{p['discount_amount']:,.0f} VNĐ`)")
        final_val_str = f"{p['final_proposed_price']:,.0f}" if p['final_proposed_price'] > 0 else "0"
        st.write(f"- **Tổng giá trị đề xuất sau CK:** `{final_val_str} VNĐ`")
        st.write(f"- **Ngân sách khách hàng:** `{p['budget']:,.0f} VNĐ`" if p['budget'] > 0 else "- **Ngân sách:** `Chưa khai báo (Missing)`")

    with col_p2:
        st.markdown("#### 3. Căn cứ Nghiệp vụ & Bước xử lý")
        st.info(f"**Bước xử lý tiếp theo:**\n{curr_dossier['next_action']}")
        if p["approval_reasons"]:
            st.warning("**Căn cứ yêu cầu phê duyệt / Cảnh báo:**\n" + "\n".join([f"- {r}" for r in p["approval_reasons"]]))

    st.markdown("---")

    # Khu vực Human-In-The-Loop: Email & Phiếu trình ký
    col_doc1, col_doc2 = st.columns(2)

    with col_doc1:
        st.markdown("#### ✉️ Bản nháp Email gửi Khách hàng")
        st.caption("AI Agent đã tự động soạn thảo dự thảo email theo trạng thái và tình huống thực tế:")
        st.text_area(
            label="Nội dung Email (NVKD có thể rà soát trước khi bấm gửi):",
            value=curr_dossier["draft_email"],
            height=300,
            key=f"email_{curr_dossier['opportunity_id']}"
        )
        if st.button("🚀 NVKD Xác nhận & Gửi Email", key=f"btn_send_{curr_dossier['opportunity_id']}"):
            st.success(f"Đã ghi nhận gửi email phản hồi tới {curr_dossier['customer_name']}!")

    with col_doc2:
        st.markdown("#### 📝 Phiếu Chuyển duyệt Trưởng phòng")
        if curr_dossier["approval_slip"]:
            st.caption(f"Hồ sơ vượt thẩm quyền NVKD, cần Trưởng phòng ({SALES_MANAGER['name']}) phê duyệt:")
            st.text_area(
                label="Nội dung Phiếu trình ký duyệt:",
                value=curr_dossier["approval_slip"],
                height=300,
                key=f"slip_{curr_dossier['opportunity_id']}"
            )
            col_app1, col_app2 = st.columns(2)
            with col_app1:
                if st.button("✅ Trưởng phòng Phê duyệt", key=f"btn_app_{curr_dossier['opportunity_id']}", type="primary"):
                    st.success("Trưởng phòng đã PHÊ DUYỆT chính sách ngoại lệ cho cơ hội này!")
            with col_app2:
                if st.button("❌ Trưởng phòng Từ chối", key=f"btn_rej_{curr_dossier['opportunity_id']}"):
                    st.error("Trưởng phòng đã TỪ CHỐI đề xuất ngoại lệ.")
        else:
            st.info("Cơ hội này nằm hoàn toàn trong hạn mức tự quyết của NVKD. Không cần tạo Phiếu chuyển duyệt!")


# ================= TAB 3: TRACE LOGS & BẰNG CHỨNG THỰC THI =================
with tab3:
    st.subheader("🔍 Nhật ký Truy vết Thực thi của AI Agent (Execution Trace Logs)")
    st.markdown("""
    > [!IMPORTANT]
    > **Bằng chứng kiểm toán quy trình AI301:** Minh chứng Agent tự động đọc dữ liệu, phân tích điều kiện, gọi công cụ nghiệp vụ (`Tool Calling`), kích hoạt quy tắc (`Rules Engine`) và xuất kết quả chứ không nhập tay kết luận.
    """)

    all_traces = GlobalTraceRegistry.get_all()
    if not all_traces:
        st.warning("Chưa có nhật ký truy vết nào.")
    else:
        trace_options = [f"Trace #{t.request_id} - {t.customer_name} ({t.final_status})" for t in all_traces]
        sel_trace_idx = st.selectbox("Chọn trace của yêu cầu cần kiểm toán:", range(len(trace_options)), format_func=lambda i: trace_options[i])

        trace_obj = all_traces[sel_trace_idx]
        t_data = trace_obj.to_dict()

        c_t1, c_t2, c_t3, c_t4 = st.columns(4)
        c_t1.metric("Mã Yêu cầu", t_data["request_id"])
        c_t2.metric("Số bước quy trình", t_data["steps_count"])
        c_t3.metric("Số công cụ đã gọi (Tools)", t_data["tools_called_count"])
        c_t4.metric("Số quy tắc áp dụng (Rules)", t_data["rules_count"])

        st.markdown("#### 1. Các Quy tắc Nghiệp vụ đã Kích hoạt (Rules Fired)")
        if t_data["rules_triggered"]:
            df_rules = pd.DataFrame(t_data["rules_triggered"])
            st.dataframe(df_rules, use_container_width=True, hide_index=True)
        else:
            st.info("Không có cảnh báo vi phạm quy tắc.")

        st.markdown("#### 2. Lịch sử Gọi Công cụ Nghiệp vụ (Tool Executions)")
        if t_data["tools_called"]:
            for call_idx, tool in enumerate(t_data["tools_called"]):
                with st.expander(f"🔧 Tool #{call_idx+1}: {tool['tool_name']} lúc {tool['timestamp']}"):
                    st.write("**Tham số truyền vào (Arguments):**")
                    st.json(tool["arguments"])
                    st.write("**Kết quả trả về từ Hệ thống (Result):**")
                    st.json(tool["result"])
        else:
            st.info("Không có lời gọi công cụ nào.")

        st.markdown("#### 3. Nhật ký Từng bước Xử lý (Step-by-step Trace)")
        for stp in t_data["steps"]:
            with st.container():
                st.markdown(f"**Bước:** `{stp['step_name']}` - *{stp['description']}* (Thời gian: {stp['timestamp']})")
                c_in, c_out = st.columns(2)
                with c_in:
                    st.caption("Inputs:")
                    st.json(stp["inputs"])
                with c_out:
                    st.caption("Outputs:")
                    st.json(stp["outputs"])
                st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)


# ================= TAB 4: DANH MỤC & KHO VẬN HÀNH =================
with tab4:
    st.subheader("🏢 Cơ sở Dữ liệu Tri thức Minh An (Catalog & Operations)")

    c_cat1, c_cat2 = st.columns([3, 2])
    with c_cat1:
        st.markdown("#### 📦 Danh mục Sản phẩm & Bảng giá Niêm yết (Q1/2026)")
        df_catalog = KnowledgeBase.get_catalog_df()
        st.dataframe(
            df_catalog[["sku", "name", "category", "list_price", "available_stock", "restock_lead_time_days", "sla_delivery_days"]].rename(columns={
                "sku": "Mã SKU",
                "name": "Tên Thiết bị / Dịch vụ",
                "category": "Phân loại",
                "list_price": "Giá Niêm yết (VNĐ)",
                "available_stock": "Tồn kho tức thì",
                "restock_lead_time_days": "Lead-time nhập thêm",
                "sla_delivery_days": "SLA giao hàng (ngày)"
            }),
            use_container_width=True,
            hide_index=True
        )

    with c_cat2:
        st.markdown("#### 👥 Đội ngũ Nhân sự Kinh doanh (6 NVKD)")
        df_reps = pd.DataFrame(SALES_REPS)
        st.dataframe(
            df_reps.rename(columns={"id": "Mã NV", "name": "Họ và Tên", "email": "Email công vụ"}),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### 📜 Chính sách Bậc thang Chiết khấu Chuẩn")
        st.markdown("""
        - **Dưới 50 triệu VNĐ:** Chiết khấu `0%`
        - **Từ 50 đến 150 triệu VNĐ:** Chiết khấu `3%`
        - **Từ 150 đến 300 triệu VNĐ:** Chiết khấu `5%` *(Hạn mức tối đa NVKD)*
        - **Trên 300 triệu VNĐ:** Chiết khấu `8%` *(Bắt buộc Trưởng phòng phê duyệt)*
        """)


# ================= TAB 5: BÁO CÁO THIẾT KẾ (TASK 1) =================
with tab5:
    st.subheader("📑 Bản Thuyết minh Thiết kế Toàn diện (Task 1 - Báo cáo AI301)")
    st.markdown("""
### 1. Phân tích Quy trình Hiện tại & 4 Vấn đề Cốt lõi
Trong mô hình hoạt động hiện tại của Công ty Minh An, 6 NVKD xử lý khoảng 180 yêu cầu/tuần (trung bình 30 yêu cầu/người/tuần). Việc thực hiện thủ công 100% bằng sức người đã bộc lộ các vấn đề nghiêm trọng:

1. **Vấn đề 1: Bỏ sót hạng mục sản phẩm trong email/form phức tạp**
   - *Nguyên nhân:* Yêu cầu khách hàng gửi dưới dạng văn bản tự do, trộn lẫn nhiều hạng mục phần cứng, phần mềm và dịch vụ triển khai.
   - *Ảnh hưởng:* Báo giá thiếu hạng mục dẫn tới thất thoát doanh thu, khách hàng phản ánh thiếu chuyên nghiệp và công ty phải báo giá lại làm kéo dài chu kỳ bán hàng.
2. **Vấn đề 2: Sử dụng đơn giá cũ và chiết khấu sai chính sách**
   - *Nguyên nhân:* Bảng giá thiết bị công nghệ và license thay đổi theo quý, NVKD tra cứu file excel cá nhân lưu cục bộ thay vì hệ thống tập trung.
   - *Ảnh hưởng:* Báo giá thấp hơn giá vốn gây xói mòn biên lợi nhuận, hoặc báo giá cao hơn thị trường làm mất cơ hội vào tay đối thủ.
3. **Vấn đề 3: Cam kết thời hạn triển khai không khả thi (Lead-time vi phạm)**
   - *Nguyên nhân:* NVKD không đối chiếu với số lượng tồn kho khả dụng và thời gian đặt hàng bổ sung của bộ phận Vận hành.
   - *Ảnh hưởng:* Chậm tiến độ giao hàng, bị phạt hợp đồng, khủng hoảng truyền thông và gây xung đột nội bộ giữa Kinh doanh và Vận hành.
4. **Vấn đề 4: Yêu cầu thiếu ngân sách / vượt quyền bị chuyển qua lại, đùn đẩy trách nhiệm**
   - *Nguyên nhân:* Thiếu người theo dõi (Lead ownership) và không có quy tắc phân loại tự động ngay từ cổng tiếp nhận.
   - *Ảnh hưởng:* Khách hàng chờ đợi quá lâu, tỷ lệ chuyển đổi cơ hội (Win rate) sụt giảm mạnh.

---

### 2. Quy trình Đề xuất Cải tiến (Đầu vào - Công việc - Đầu ra - Trách nhiệm)
Bám sát mô hình luồng công việc tối ưu cho Công ty Minh An:

| Bước | Tên Bước | Đầu vào (Input) | Công việc thực hiện | Đầu ra (Output) | Bộ phận chịu trách nhiệm |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Tiếp nhận yêu cầu | Email, Web Form, File Excel/CSV, Link Google Sheet | Thu thập dữ liệu thô đa kênh, gán định danh duy nhất (Request ID) | Bản ghi yêu cầu thô được chuẩn hóa | **AI Agent** |
| **B2** | Phân loại & Kiểm tra thông tin | Bản ghi yêu cầu thô | Bóc tách thực thể (Sản phẩm, số lượng, deadline, ngân sách), kiểm tra tính đầy đủ | Cờ hợp lệ (`is_complete`), danh sách trường thiếu | **AI Agent** |
| **B3** | Xử lý yêu cầu thiếu dữ liệu | Danh sách trường thiếu | Tự động tạo bản nháp email lịch sự xin bổ sung thông tin gửi khách | Bản nháp Email yêu cầu làm rõ | **AI Agent** (NVKD kiểm tra & gửi) |
| **B4** | Tạo Hồ sơ & Gắn phụ trách | Dữ liệu đầy đủ hợp lệ | Tạo mã hồ sơ cơ hội (OPP-ID), phân bổ đều (Round-robin) cho 6 NVKD | Hồ sơ cơ hội sơ bộ có người chịu trách nhiệm | **AI Agent** |
| **B5** | Thẩm định tồn kho & giá | Danh mục sản phẩm yêu cầu | Tra cứu Catalog chuẩn, kiểm tra tồn kho tức thì, tính toán lead-time khả dụng | Báo cáo khả thi vận hành & Bảng đơn giá niêm yết | **AI Agent + Tool Vận hành** |
| **B6** | Lập Báo giá & Dự thảo đề xuất | Báo cáo khả thi & Chính sách | Áp chiết khấu theo bậc thang doanh số, so sánh ngân sách khách hàng | Dự thảo báo giá & Đánh giá vượt thẩm quyền | **AI Agent** |
| **B7** | Phê duyệt vượt thẩm quyền | Dự thảo báo giá vượt hạn mức | Soát xét rủi ro, biên lợi nhuận và phê duyệt chính sách đặc biệt | Quyết định phê duyệt (Duyệt / Từ chối / Đàm phán) | **Trưởng phòng Kinh doanh (HITL)** |
| **B8** | Cập nhật & Theo dõi | Kết quả duyệt & Dự thảo email | Xuất Hồ sơ cơ hội hoàn chỉnh, gửi email báo giá cho khách, theo dõi tiến độ | Hồ sơ đóng vết, Email báo giá gửi đi | **NVKD phụ trách + AI Agent** |

---

### 3. Lựa chọn 3 Bước AI Agent Tự Thực Hiện & Rationale
1. **Bước 2: Phân loại & Bóc tách thực thể tự động (Intake & Entity Extraction):**
   - *Lý do:* Giải quyết triệt để vấn đề con người đọc sót thông tin từ email dài; chuyển đổi dữ liệu phi cấu trúc thành dữ liệu có cấu trúc với tốc độ tính bằng mili-giây.
2. **Bước 5: Thẩm định khả năng đáp ứng Tồn kho & SLA Giao hàng (Feasibility Matching):**
   - *Lý do:* Tự động gọi API tra cứu kho và SLA của bộ phận Vận hành theo thời gian thực; loại bỏ hoàn toàn việc NVKD tự hứa thời hạn phi thực tế.
3. **Bước 6: Áp bảng giá niêm yết, tính chiết khấu & Kiểm tra quy tắc thẩm quyền (Pricing & Policy Rules Engine):**
   - *Lý do:* Đảm bảo 100% cơ hội đều áp dụng bảng giá mới nhất; ngăn chặn tình trạng bán dưới giá sàn và tự động phát hiện các case vượt quyền để chuyển duyệt.

---

### 4. Hai Điểm Con Người Kiểm Soát (Human-In-The-Loop - HITL) & Guardrails
- **Điểm HITL 1: Trưởng phòng Kinh doanh Phê duyệt Vượt thẩm quyền:**
  - *Điều kiện chuyển xử lý:* Khi đơn hàng có tổng giá trị > 300 triệu VNĐ, chiết khấu khách yêu cầu > 5% (hoặc vượt bậc tiêu chuẩn), hoặc ngân sách khách thấp hơn giá sàn.
  - *Cơ chế:* Agent không tự xác nhận bán mà tự động lập *Phiếu trình ký* kèm đầy đủ phân tích tài chính để Trưởng phòng bấm duyệt hoặc từ chối.
- **Điểm HITL 2: NVKD Phụ trách Rà soát & Xác nhận Gửi Email:**
  - *Điều kiện chuyển xử lý:* Khi hồ sơ ở trạng thái "Cần bổ sung thông tin" hoặc "Chưa đáp ứng" hoặc sau khi có phê duyệt.
  - *Cơ chế:* Agent soạn sẵn bản nháp cá nhân hóa; NVKD đọc lại ngữ cảnh, bổ sung trao đổi mang tính quan hệ khách hàng và bấm gửi.
- **Cơ chế Phát hiện Kết quả Sai (Error Detection & Guardrails):**
  - Schema Validation: Kiểm tra kiểu dữ liệu và số lượng > 0.
  - SKU Exact/Fuzzy Matching: Nếu sản phẩm không có trong Catalog chuẩn, Agent đánh dấu cảnh báo `UNKNOWN` và chặn tạo báo giá tự động.
  - Boundary Checking: Kiểm tra logic chênh lệch ngân sách và biên lợi nhuận.
  - Toàn bộ hành vi được ghi nhật ký (Trace logs) minh bạch.
    """)
