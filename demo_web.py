"""Web demo offline cho Medical Appointment ReAct Agent.

Chạy: python demo_web.py
Sau đó mở: http://127.0.0.1:8000
"""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import demo_cli
from tools import dispatch_tool_call


ROOT = Path(__file__).parent


class DemoHandler(SimpleHTTPRequestHandler):
    """Phục vụ giao diện tĩnh và hai API nhỏ cho phiên demo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.path = "/web_demo.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/reset":
            demo_cli.reset_session()
            return self.respond_json({"ok": True})
        if path != "/api/chat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            user_text = str(payload.get("message", "")).strip()
            if not user_text:
                raise ValueError("Vui lòng nhập câu hỏi.")

            decision = demo_cli.decide(user_text)
            trace = [{"label": "Thought", "icon": "🧠", "content": decision["thought"], "kind": "thought"}]
            if decision["type"] == "text":
                final_answer = decision["content"]
            else:
                tool, arguments = decision["tool"], decision["arguments"]
                trace.append({
                    "label": "Action Proposed", "icon": "🛠️", "kind": "action",
                    "content": f"{tool}({json.dumps(arguments, ensure_ascii=False)})",
                })
                observation = json.loads(dispatch_tool_call(tool, arguments))
                trace.append({
                    "label": "Observation", "icon": "👁️", "kind": "observation",
                    "content": json.dumps(observation, ensure_ascii=False, indent=2),
                })
                final_answer = demo_cli.synthesize(tool, arguments, observation)

            trace.append({"label": "Final Answer", "icon": "🏁", "content": final_answer, "kind": "final"})
            self.respond_json({"answer": final_answer, "trace": trace})
        except (ValueError, json.JSONDecodeError) as error:
            self.respond_json({"error": str(error)}, status=400)
        except Exception as error:  # Giữ giao diện chạy khi demo có lỗi bất ngờ.
            self.respond_json({"error": f"Không thể xử lý yêu cầu: {error}"}, status=500)

    def respond_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DemoHandler)
    print("✨ ReAct web demo đang chạy tại http://127.0.0.1:8000")
    print("Nhấn Ctrl+C để dừng máy chủ.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng web demo.")
    finally:
        server.server_close()
