# HỆ THỐNG AI AGENT XỬ LÝ CƠ HỘI BÁN HÀNG B2B - MINH AN COMPANY
**Học phần:** AI301 AI AGENT | **Đề án 01**

---

## 🌟 Tổng quan Đề tài
Dự án xây dựng giải pháp **AI Agent tự động hóa quy trình xử lý cơ hội bán hàng B2B** cho Công ty Cổ phần Công nghệ Minh An. Hệ thống tiếp nhận các yêu cầu báo giá/triển khai công nghệ từ khách hàng qua nhiều kênh (File Excel, File CSV, Link Google Sheets), tự động bóc tách thực thể, thẩm định tồn kho và thời gian cung ứng với bộ phận Vận hành, áp bảng giá niêm yết và chính sách chiết khấu chuẩn, kiểm tra hạn mức thẩm quyền của Nhân viên Kinh doanh (NVKD) và xuất Hồ sơ cơ hội (Dossier), Bản nháp Email phản hồi cùng Phiếu trình ký Trưởng phòng.

---

## 🛠️ Cấu trúc Mã nguồn

```text
Agent QTKD2/
├── app.py                  # Giao diện Web Dashboard tương tác (Streamlit)
├── config.py               # Cấu hình danh sách 6 NVKD, Trưởng phòng, Quy tắc thẩm quyền & Bậc chiết khấu
├── knowledge_base.py       # Tri thức chuẩn: Bảng giá niêm yết (Catalog), Tồn kho khả dụng & SLA Vận hành
├── agent_skills.py         # 4 Kỹ năng nghiệp vụ phối hợp trong Pipeline AI Agent
├── pipeline.py             # Orchestrator điều phối toàn trình (End-to-End Execution Pipeline)
├── data_loader.py          # Module nạp dữ liệu đa kênh (Excel .xlsx, CSV, Google Sheets URL)
├── trace_logger.py         # Hệ thống Audit Trace: Lưu nhật ký từng bước, Tool calls, Rules kích hoạt
├── test_agent.py           # Bộ kiểm thử tự động (Unit Test Suite) 100% Passed
├── sample_data/            # Dữ liệu mẫu chuẩn cấu trúc phục vụ thi cử & demo
│   ├── sample_requests.xlsx
│   └── sample_requests.csv
└── README.md               # Tài liệu thuyết minh & Hướng dẫn sử dụng
```

---

## 🚀 Hướng dẫn Chạy Ứng dụng

1. **Khởi chạy Giao diện Streamlit:**
   ```bash
   streamlit run app.py
   ```
   Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: `http://localhost:8501`

2. **Chạy Bộ kiểm thử tự động (Unit Tests):**
   ```bash
   python test_agent.py
   ```

---

## 📥 Hướng dẫn Nạp Dữ liệu Đầu vào

Hệ thống hỗ trợ 3 hình thức nạp dữ liệu linh hoạt trên giao diện Sidebar:
1. **Dùng Bộ dữ liệu mẫu tích hợp sẵn (8 Cases):** Bao gồm đủ 4 nhóm trường hợp theo yêu cầu đề thi (Thông thường, Thiếu dữ liệu, Chưa đáp ứng, Chờ duyệt).
2. **Tải lên File:** Kéo thả file `.xlsx` hoặc `.csv`.
3. **Dán link Google Sheets:** Dán đường link Google Sheets công khai (Quyền *Anyone with the link can view*). Agent sẽ tự động chuyển đổi sang CSV stream và nạp trực tiếp vào pipeline.

---

## 🎯 Task 1: Thiết kế Quy trình & Phân tích Nghiệp vụ
*(Xem chi tiết tại Tab "📑 Thuyết minh Thiết kế (Task 1)" trên giao diện ứng dụng hoặc tài liệu báo cáo).*

1. **4 Vấn đề cốt lõi trong bối cảnh hiện tại:**
   - *Bỏ sót hạng mục sản phẩm:* Khách gửi email văn bản tự do nhiều dòng/sản phẩm.
   - *Dùng giá cũ & chiết khấu sai lệch:* Không đồng bộ bảng giá niêm yết mới nhất, xói mòn biên lợi nhuận.
   - *Cam kết thời hạn (Lead time) không khả thi:* NVKD không đối chiếu với tồn kho và thời gian cung ứng của Vận hành, dẫn đến chậm tiến độ, bị phạt hợp đồng.
   - *Yêu cầu thiếu dữ liệu/vượt quyền bị chuyển qua lại (Orphaned leads):* Thiếu người phụ trách rõ ràng, kéo dài thời gian phản hồi.

2. **3 Bước AI Agent tự thực hiện:**
   - *Bước 1: Tiếp nhận, Bóc tách thực thể & Kiểm tra tính đầy đủ của thông tin*
   - *Bước 2: Thẩm định khả năng đáp ứng Tồn kho & SLA Thời gian triển khai* (gọi API kho Vận hành)
   - *Bước 3: Tra cứu bảng giá chuẩn, tính chiết khấu & Kiểm tra quy tắc thẩm quyền* (Policy Engine)

3. **2 Điểm Con người Kiểm soát (Human-in-the-Loop):**
   - *Điểm HITL 1: Trưởng phòng Kinh doanh Phê duyệt Vượt thẩm quyền* (Đơn > 300 triệu, Chiết khấu > 5%, Ngân sách thấp hơn giá sàn).
   - *Điểm HITL 2: NVKD Rà soát & Xác nhận gửi Email phản hồi* (Đặc biệt các case xin bổ sung thông tin hoặc đàm phán lại lead time).

