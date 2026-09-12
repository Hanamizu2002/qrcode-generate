#!/usr/bin/env python3
"""QR code HTTP API. Run: python api_server.py"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from url_to_svg import generate_svg, svg_to_png


class Handler(BaseHTTPRequestHandler):
    server_version = "QRStudio/1.0"

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        elif self.path == "/generate":
            self.method_not_allowed("POST, OPTIONS")
        else:
            self.send_json(404, {"error": "接口不存在。"})

    def do_POST(self):
        if self.path == "/health":
            self.method_not_allowed("GET, OPTIONS")
            return
        if self.path != "/generate":
            self.send_json(404, {"error": "接口不存在。"})
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Content-Type 必须是 application/json。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16_384:
                raise ValueError("请求内容过大或为空。")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("请求体必须是 JSON 对象。")
            output_format = data.get("format", "svg")
            if output_format not in ("svg", "png"):
                raise ValueError("输出格式必须是 svg 或 png。")
            size = data.get("size", 1024)
            svg, ratio, version = generate_svg(
                data.get("url", ""), size=size, border=data.get("border", 4),
                center_ratio=data.get("center_ratio", 1 / 3),
                color=data.get("color", "#000000"))
            if output_format == "svg":
                body, content_type = svg.encode(), "image/svg+xml; charset=utf-8"
            else:
                body, content_type = svg_to_png(svg, size), "image/png"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="qrcode.{output_format}"')
            self.send_header("X-QR-Version", str(version))
            self.send_header("X-QR-Error-Correction", "H")
            self.send_header("X-Center-Ratio", f"{ratio:.3f}")
            self.send_header("X-QR-Color", data.get("color", "#000000").upper())
            self.security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (json.JSONDecodeError, TypeError, ValueError, OverflowError) as exc:
            self.send_json(400, {"error": str(exc)})
        except (ImportError, OSError) as exc:
            self.send_json(500, {"error": f"生成环境错误：{exc}"})

    def do_PUT(self):
        self.method_not_allowed("GET, POST, OPTIONS")

    do_PATCH = do_PUT
    do_DELETE = do_PUT

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.security_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.security_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def method_not_allowed(self, allow):
        body = json.dumps({"error": "请求方法不受支持。"}, ensure_ascii=False).encode()
        self.send_response(405)
        self.send_header("Allow", allow)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.security_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def log_message(self, message, *args):
        print(f"[{self.log_date_time_string()}] {message % args}")


def main():
    parser = argparse.ArgumentParser(description="启动二维码生成 API")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"二维码 API 已启动：http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
