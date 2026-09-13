"""Demo CLI offline cho Trợ lý Đặt lịch Khám bệnh & FAQ.

Chạy: python demo_cli.py
Không cần API key. Nhập ``reset`` để khôi phục dữ liệu mẫu, hoặc
``exit``/``quit`` để thoát. Demo hiển thị chuỗi ReAct:
Thought -> Action -> Observation -> Final Answer.
"""

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
if sys.stdin.encoding != "utf-8":
    try:
        sys.stdin.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools import MOCK_DATABASE, dispatch_tool_call  # noqa: E402


INITIAL_DATABASE = copy.deepcopy(MOCK_DATABASE)
pending_booking: dict[str, str] = {}


def reset_session() -> None:
    """Khôi phục lịch trống và xóa lịch đã đặt trong phiên demo."""
    global pending_booking
    MOCK_DATABASE.clear()
    MOCK_DATABASE.update(copy.deepcopy(INITIAL_DATABASE))
    pending_booking = {}
    print("🔄 Đã đặt lại phiên: lịch hẹn đã xóa, lịch trống đã được khôi phục.")


def extract_date(text: str) -> str:
    iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso:
        return iso.group(1)
    vietnamese = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if vietnamese:
        day, month, year = vietnamese.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return ""


def extract_specialty(text: str) -> str:
    normalized = text.lower()
    for specialty in ("Tim mạch", "Tiêu hóa", "Nhi khoa"):
        if specialty.lower() in normalized:
            return specialty
    if re.search(r"\bnhi\b", normalized):
        return "Nhi khoa"
    return ""


def extract_doctor_id(text: str) -> str:
    match = re.search(r"\bBS0*([1-3])\b", text.upper())
    return f"BS00{match.group(1)}" if match else ""


def extract_time(text: str) -> str:
    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    return f"{match.group(1).zfill(2)}:{match.group(2)}" if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r"\b0\d{9,10}\b", text)
    return match.group(0) if match else ""


def extract_name(text: str) -> str:
    match = re.search(r"(?:tên|tôi là)\s*(?:là|:)??\s*([^,.;\n]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_booking_id(text: str) -> str:
    match = re.search(r"\bMED-\d{3,5}\b", text.upper())
    return match.group(0) if match else ""


def decide(user_text: str) -> dict[str, Any]:
    """Mô phỏng phần quyết định của LLM để demo luôn chạy offline."""
    lowered = user_text.lower()
    booking_id = extract_booking_id(user_text)

    if booking_id and re.search(r"hủy|huỷ", lowered):
        return tool_decision("cancel_appointment", booking_id=booking_id)
    if booking_id and re.search(r"kiểm tra|tra cứu|xem|trạng thái", lowered):
        return tool_decision("check_booking", booking_id=booking_id)
    if re.search(r"giờ làm việc|mở cửa|làm việc", lowered):
        return faq_decision(user_text, "working_hours")
    if "bảo hiểm" in lowered:
        return faq_decision(user_text, "insurance")
    if re.search(r"lần đầu|thủ tục khám|giấy tờ", lowered):
        return faq_decision(user_text, "first_visit_procedure")
    if re.search(r"chính sách|quy định|bao lâu|bao nhiêu giờ|ít nhất", lowered) and re.search(r"hủy|huỷ", lowered):
        return faq_decision(user_text, "cancellation_policy")
    if re.search(r"hủy|huỷ", lowered):
        return tool_decision("cancel_appointment", booking_id=pending_booking.get("booking_id", ""))

    is_booking = bool(re.search(r"đặt lịch|đặt hẹn|book", lowered)) or bool(pending_booking)
    if is_booking:
        details = dict(pending_booking)
        specialty = extract_specialty(user_text)
        doctor_id = extract_doctor_id(user_text)
        if specialty and not doctor_id:
            doctor_id = next((d["doctor_id"] for d in MOCK_DATABASE["doctors"] if d["specialty"] == specialty), "")
        for key, value in {
            "doctor_id": doctor_id, "date": extract_date(user_text), "time_slot": extract_time(user_text),
            "phone": extract_phone(user_text), "patient_name": extract_name(user_text),
        }.items():
            if value:
                details[key] = value
        return tool_decision("book_appointment", **details)

    if re.search(r"lịch trống|còn lịch|khung giờ", lowered):
        specialty = extract_specialty(user_text)
        doctor_id = extract_doctor_id(user_text) or next(
            (d["doctor_id"] for d in MOCK_DATABASE["doctors"] if d["specialty"] == specialty), "BS001"
        )
        return tool_decision("check_availability", doctor_id=doctor_id, date=extract_date(user_text) or "2026-09-15")
    if re.search(r"bác sĩ|tim mạch|tiêu hóa|nhi khoa", lowered):
        return tool_decision("search_doctors", specialty=extract_specialty(user_text))
    return {
        "type": "text",
        "thought": "Câu hỏi chung, không cần truy vấn dữ liệu hệ thống.",
        "content": "Tôi có thể tìm bác sĩ, kiểm tra lịch trống, đặt/tra cứu/hủy lịch và giải đáp quy định bệnh viện.",
    }


def tool_decision(action: str, **arguments: str) -> dict[str, Any]:
    return {
        "type": "tool_call",
        "tool": "manage_appointment",
        "arguments": {"action": action, **arguments},
        "thought": f"Yêu cầu cần dữ liệu lịch khám; tôi sẽ gọi manage_appointment với action={action}.",
    }


def faq_decision(question: str, category: str) -> dict[str, Any]:
    return {
        "type": "tool_call", "tool": "get_faq",
        "arguments": {"question": question, "category": category},
        "thought": "Câu hỏi thuộc quy định bệnh viện; tôi sẽ tra cứu FAQ.",
    }


def synthesize(tool: str, arguments: dict[str, str], observation: dict[str, Any]) -> str:
    global pending_booking
    if tool == "get_faq":
        return observation.get("answer") or observation.get("message", "Không có câu trả lời phù hợp.")

    action = arguments["action"]
    if action == "search_doctors":
        if observation["status"] != "SUCCESS":
            return observation["message"]
        doctors = observation["doctors"]
        return "Tìm thấy:\n" + "\n".join(
            f"• {d['name']} — {d['specialty']} ({d['location']}, mã {d['doctor_id']})" for d in doctors
        )
    if action == "check_availability":
        if observation["status"] != "SUCCESS":
            return observation["message"]
        slots = observation["available_slots"]
        if not slots:
            return f"{observation['doctor']['name']} không còn lịch trống ngày {observation['date']}."
        return f"{observation['doctor']['name']} còn trống ngày {observation['date']}: {', '.join(slots)}."
    if action == "book_appointment":
        if observation["status"] == "MISSING_INFORMATION":
            pending_booking = {k: v for k, v in arguments.items() if k != "action"}
            missing = observation["message"].replace("Thiếu thông tin: ", "").rstrip(".")
            return f"Cần thêm: {missing}. Bạn cung cấp giúp tôi nhé?"
        if observation["status"] != "SUCCESS":
            return observation.get("message", json.dumps(observation, ensure_ascii=False))
        pending_booking = {}
        appointment = observation["appointment"]
        return (f"Đặt lịch thành công! Mã: {appointment['booking_id']}. {appointment['patient_name']} khám với "
                f"{appointment['doctor_id']} lúc {appointment['time_slot']} ngày {appointment['date']}.")
    if action == "check_booking" and observation["status"] == "SUCCESS":
        appointment = observation["appointment"]
        return (f"Lịch {appointment['booking_id']}: {appointment['patient_name']}, bác sĩ {appointment['doctor_id']}, "
                f"{appointment['date']} lúc {appointment['time_slot']}, trạng thái {appointment['status']}.")
    if action == "cancel_appointment" and observation["status"] == "SUCCESS":
        return f"Đã hủy lịch hẹn {observation['appointment']['booking_id']} thành công."
    if action == "cancel_appointment" and not arguments.get("booking_id"):
        return observation.get("message", "Không tìm thấy lịch hẹn.") + " Hãy cung cấp mã, ví dụ MED-0001."
    return observation.get("message", json.dumps(observation, ensure_ascii=False))


def run_agent(user_text: str) -> None:
    decision = decide(user_text)
    print(f"🧠 [Thought]: {decision['thought']}")
    if decision["type"] == "text":
        print(f"🏁 [Final Answer]: {decision['content']}")
        return
    tool, arguments = decision["tool"], decision["arguments"]
    print(f"🛠️  [Action Proposed]: {tool}({json.dumps(arguments, ensure_ascii=False)})")
    observation = json.loads(dispatch_tool_call(tool, arguments))
    print(f"👁️  [Observation]: {json.dumps(observation, ensure_ascii=False)}")
    print(f"🏁 [Final Answer]: {synthesize(tool, arguments, observation)}")


def main() -> None:
    examples = [
        "Bệnh viện làm việc giờ nào?",
        "Tìm bác sĩ Tim mạch",
        "BS001 còn lịch trống ngày 2026-09-15 không?",
        "Tôi muốn đặt lịch với BS001 ngày 2026-09-15 lúc 09:00, tên Nguyễn Văn Minh, số 0901234567",
        "Kiểm tra lịch hẹn MED-0001",
        "Hủy lịch hẹn MED-0001",
    ]
    print("=" * 66)
    print("🤖 DEMO CLI — ReAct Agent Đặt lịch Khám bệnh (offline)")
    print("=" * 66)
    print("Gợi ý: " + " | ".join(examples[:3]))
    print("Gõ 'reset' để làm lại phiên; 'exit' hoặc 'quit' để thoát.\n")
    while True:
        try:
            user_text = input("👤 Bạn hỏi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã thoát.")
            return
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("👋 Tạm biệt!")
            return
        if user_text.lower() == "reset":
            reset_session()
        else:
            run_agent(user_text)
        print()


if __name__ == "__main__":
    main()
