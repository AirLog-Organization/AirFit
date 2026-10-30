"""로컬 개발 서버. Docker 없이 lambda_handler를 http://localhost:3000 에 띄운다.

    .venv/bin/python dev_server.py

키는 backend/.env에서 읽는다. 배포에는 쓰이지 않는다.
"""

import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
PORT = 3000


def load_env(path: Path) -> None:
    if not path.exists():
        sys.exit(f"{path}가 없습니다. .env.example을 복사해 키를 채워 주세요.")
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        event = {
            "rawPath": url.path,
            "queryStringParameters": dict(urllib.parse.parse_qsl(url.query)) or None,
            "requestContext": {"http": {"method": "GET"}},
        }
        response = lambda_handler(event, None)
        body = response["body"].encode()
        self.send_response(response["statusCode"])
        for key, value in response["headers"].items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    load_env(BACKEND_DIR / ".env")
    sys.path.insert(0, str(BACKEND_DIR / "src"))
    from airfit.handler import lambda_handler

    print(f"http://localhost:{PORT}/api/health")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
