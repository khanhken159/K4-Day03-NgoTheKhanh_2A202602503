# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** [Điền Họ và Tên]    Ngô Thế Khanh 
> **Mã Sinh Viên / Mã Học viên:** [Điền MSSV]  2A202602503
> **Chủ đề Lựa chọn:** [Điền tên chủ đề đã chọn từ docs/DANH_SACH_DE_TAI.md hoặc Đề tài Mở]  Đề tài mở : "Trợ lý Ảo Đặt lịch Khám bệnh & Tư vấn Quy định (Medical Appointment & FAQ Assistant)

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** |5 / 5 | Agent cần xác định nhu cầu khám, thu thập chuyên khoa, ngày giờ và thông tin bệnh nhân trước khi đặt lịch.
| **2. Tool Interaction** |5 / 5 | Cần gọi tool tra cứu lịch bác sĩ, kiểm tra khung giờ trống và tạo lịch hẹn.
| **3. Dynamic Decision** | 4/ 5 | Nếu bác sĩ hoặc khung giờ không khả dụng, Agent phải dựa vào kết quả tool để đề xuất lựa chọn khác.
| **4. Long Horizon Goal** | 3/ 5 | Mục tiêu xuyên suốt là hoàn tất lịch khám chính xác, nhưng thường chỉ trong một phiên hội thoại ngắn
| **TỔNG ĐIỂM AGENTIC FIT** | 16**/ 20** | Phù hợp để triển khai ReAct Agent vì có tool calling và quyết định dựa trên dữ liệu thực tế.

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG

### Test case tiêu biểu: Đặt lịch khám Tim mạch

**Câu hỏi:** Hãy đặt lịch khám Tim mạch cho tôi vào ngày 2026-09-15 lúc 09:00.

```json
{
  "step": 1,
  "query": "Hãy đặt lịch khám Tim mạch cho tôi vào ngày 2026-09-15 lúc 09:00.",
  "action_type": "TOOL_EXECUTION",
  "tool_name": "manage_appointment",
  "arguments": {
    "action": "book_appointment",
    "patient_name": "Nguyễn Văn Minh",
    "phone": "0901234567",
    "doctor_id": "BS001",
    "date": "2026-09-15",
    "time_slot": "09:00"
  },
  "observation": {
    "status": "SUCCESS",
    "appointment": {
      "booking_id": "MED-0001",
      "patient_name": "Nguyễn Văn Minh",
      "doctor_id": "BS001",
      "date": "2026-09-15",
      "time_slot": "09:00",
      "status": "BOOKED"
    },
    "message": "Đặt lịch khám thành công."
  }
}

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5/ 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
