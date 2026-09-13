"""
TOOL DEFINITIONS & EXECUTION BACKEND
Tools for the Medical Appointment & FAQ Assistant.
"""

import json
from typing import Any, Dict

# ============================================================================
# 1. TOOL SCHEMAS
# ============================================================================

TOOLS_SCHEMA = [
    {
        "name": "get_faq",
        "description": (
            "Trả lời câu hỏi về nội quy, chính sách và quy trình của bệnh viện: "
            "giờ làm việc, hủy lịch, bảo hiểm và thủ tục khám lần đầu."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Câu hỏi của người dùng về nội quy hoặc chính sách bệnh viện."
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "working_hours",
                        "cancellation_policy",
                        "insurance",
                        "first_visit_procedure",
                        "other"
                    ],
                    "description": "Nhóm câu hỏi (không bắt buộc)."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "manage_appointment",
        "description": (
            "Quản lý lịch khám: tìm bác sĩ, kiểm tra lịch trống, đặt lịch, "
            "kiểm tra lịch đã đặt hoặc hủy lịch."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "search_doctors",
                        "check_availability",
                        "book_appointment",
                        "check_booking",
                        "cancel_appointment"
                    ],
                    "description": "Thao tác cần thực hiện."
                },
                "specialty": {
                    "type": "string",
                    "description": "Chuyên khoa, ví dụ: Tim mạch, Tiêu hóa, Nhi khoa."
                },
                "doctor_name": {
                    "type": "string",
                    "description": "Tên bác sĩ (không bắt buộc)."
                },
                "doctor_id": {
                    "type": "string",
                    "description": "Mã bác sĩ, lấy từ kết quả tìm kiếm."
                },
                "date": {
                    "type": "string",
                    "description": "Ngày khám theo định dạng YYYY-MM-DD."
                },
                "time_slot": {
                    "type": "string",
                    "description": "Khung giờ khám, ví dụ 09:00."
                },
                "patient_name": {
                    "type": "string",
                    "description": "Họ tên bệnh nhân khi đặt lịch."
                },
                "phone": {
                    "type": "string",
                    "description": "Số điện thoại liên hệ khi đặt lịch."
                },
                "booking_id": {
                    "type": "string",
                    "description": "Mã lịch hẹn dùng để kiểm tra hoặc hủy lịch."
                }
            },
            "required": ["action"]
        }
    }
]

# ============================================================================
# 2. MOCK DATA
# ============================================================================

MOCK_DATABASE = {
    "doctors": [
        {"doctor_id": "BS001", "name": "BS. Nguyễn Minh An", "specialty": "Tim mạch", "location": "Cơ sở Quận 1"},
        {"doctor_id": "BS002", "name": "BS. Trần Thu Hà", "specialty": "Tiêu hóa", "location": "Cơ sở Quận 1"},
        {"doctor_id": "BS003", "name": "BS. Lê Hoàng Nam", "specialty": "Nhi khoa", "location": "Cơ sở Thủ Đức"}
    ],
    "availability": {
        "BS001": {"2026-09-15": ["09:00", "10:30"], "2026-09-16": ["08:30", "14:00"]},
        "BS002": {"2026-09-15": ["08:00", "13:30"], "2026-09-16": ["09:30", "15:00"]},
        "BS003": {"2026-09-15": ["09:00", "14:30"], "2026-09-16": ["08:00", "10:00"]}
    },
    "appointments": [],
    "faqs": {
        "working_hours": "Bệnh viện làm việc từ 07:30 đến 17:00, Thứ Hai đến Thứ Bảy.",
        "cancellation_policy": "Bạn có thể hủy lịch trước giờ khám ít nhất 2 giờ bằng mã lịch hẹn.",
        "insurance": "Vui lòng mang thẻ bảo hiểm y tế còn hiệu lực và giấy tờ tùy thân khi làm thủ tục.",
        "first_visit_procedure": "Khi khám lần đầu, vui lòng đến trước giờ hẹn 15 phút, mang CCCD và hồ sơ y tế nếu có."
    }
}


def _result(status: str, **data: Any) -> str:
    return json.dumps({"status": status, **data}, ensure_ascii=False)


def execute_get_faq(question: str, category: str = "other") -> str:
    """Tra cứu nội quy và câu hỏi thường gặp của bệnh viện."""
    normalized = category.lower()
    if normalized == "other":
        text = question.lower()
        if any(word in text for word in ["giờ", "mở cửa", "làm việc"]):
            normalized = "working_hours"
        elif any(word in text for word in ["hủy", "huỷ"]):
            normalized = "cancellation_policy"
        elif "bảo hiểm" in text:
            normalized = "insurance"
        elif any(word in text for word in ["lần đầu", "thủ tục", "giấy tờ"]):
            normalized = "first_visit_procedure"

    answer = MOCK_DATABASE["faqs"].get(normalized)
    if not answer:
        return _result("NOT_FOUND", message="Chưa có quy định phù hợp với câu hỏi này.")
    return _result("SUCCESS", category=normalized, answer=answer)


def execute_manage_appointment(action: str, **kwargs: Any) -> str:
    """Xử lý các thao tác tìm, kiểm tra, đặt và hủy lịch khám."""
    action = action.strip().lower()
    doctors = MOCK_DATABASE["doctors"]

    if action == "search_doctors":
        specialty = kwargs.get("specialty", "").lower()
        doctor_name = kwargs.get("doctor_name", "").lower()
        matches = [
            doctor for doctor in doctors
            if (not specialty or specialty in doctor["specialty"].lower())
            and (not doctor_name or doctor_name in doctor["name"].lower())
        ]
        if not matches:
            return _result("NOT_FOUND", message="Không tìm thấy bác sĩ phù hợp.")
        return _result("SUCCESS", doctors=matches)

    if action == "check_availability":
        doctor_id = kwargs.get("doctor_id", "").upper()
        date = kwargs.get("date", "")
        doctor = next((item for item in doctors if item["doctor_id"] == doctor_id), None)
        if not doctor:
            return _result("NOT_FOUND", message="Không tìm thấy bác sĩ theo mã đã cung cấp.")
        slots = MOCK_DATABASE["availability"].get(doctor_id, {}).get(date, [])
        return _result("SUCCESS", doctor=doctor, date=date, available_slots=slots)

    if action == "book_appointment":
        required = ["patient_name", "phone", "doctor_id", "date", "time_slot"]
        missing = [field for field in required if not kwargs.get(field)]
        if missing:
            return _result("MISSING_INFORMATION", message=f"Thiếu thông tin: {', '.join(missing)}.")
        doctor_id, date, time_slot = kwargs["doctor_id"].upper(), kwargs["date"], kwargs["time_slot"]
        slots = MOCK_DATABASE["availability"].get(doctor_id, {}).get(date, [])
        if time_slot not in slots:
            return _result("NOT_AVAILABLE", message="Khung giờ này không còn trống.")
        booking_id = f"MED-{len(MOCK_DATABASE['appointments']) + 1:04d}"
        appointment = {
            "booking_id": booking_id, "patient_name": kwargs["patient_name"],
            "phone": kwargs["phone"], "doctor_id": doctor_id, "date": date,
            "time_slot": time_slot, "status": "BOOKED"
        }
        MOCK_DATABASE["appointments"].append(appointment)
        slots.remove(time_slot)
        return _result("SUCCESS", appointment=appointment, message="Đặt lịch khám thành công.")

    if action in {"check_booking", "cancel_appointment"}:
        booking_id = kwargs.get("booking_id", "").upper()
        appointment = next((item for item in MOCK_DATABASE["appointments"] if item["booking_id"] == booking_id), None)
        if not appointment:
            return _result("NOT_FOUND", message="Không tìm thấy lịch hẹn theo mã đã cung cấp.")
        if action == "cancel_appointment":
            if appointment["status"] == "CANCELLED":
                return _result("ALREADY_CANCELLED", appointment=appointment)
            appointment["status"] = "CANCELLED"
            MOCK_DATABASE["availability"][appointment["doctor_id"]][appointment["date"]].append(appointment["time_slot"])
            return _result("SUCCESS", appointment=appointment, message="Đã hủy lịch khám thành công.")
        return _result("SUCCESS", appointment=appointment)

    return _result("INVALID_ACTION", message="Thao tác quản lý lịch không hợp lệ.")


TOOL_ROUTER = {
    "get_faq": execute_get_faq,
    "manage_appointment": execute_manage_appointment
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Điều hướng yêu cầu đến hàm thực thi tool phù hợp."""
    if tool_name not in TOOL_ROUTER:
        return _result("UNKNOWN_TOOL", error=f"Tool '{tool_name}' không tồn tại.")
    try:
        return TOOL_ROUTER[tool_name](**arguments)
    except Exception as error:
        return _result("EXECUTION_ERROR", error=str(error))
