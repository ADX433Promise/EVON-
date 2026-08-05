import os
import json
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_FILE = BASE_DIR / "data.json"

if not DATA_FILE.exists():
    DATA_FILE.write_text("{}", encoding="utf-8")


def load_data():
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.send_file("index.html")
        elif path == "/styles.css":
            self.send_file("styles.css")
        elif path == "/script.js":
            self.send_file("script.js")
        elif path.startswith("/download/"):
            token = path.split("/download/")[-1]
            data = load_data()
            entry = data.get(token)
            if not entry:
                self.send_error(404, "Not Found")
                return

            if entry.get("opens", 0) >= entry.get("limit", 1):
                self.send_error(403, "Link limit reached")
                return

            entry["opens"] = entry.get("opens", 0) + 1
            data[token] = entry
            save_data(data)

            file_path = UPLOAD_DIR / entry["filename"]
            if not file_path.exists():
                self.send_error(404, "File not found")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename={entry['filename']}")
            self.end_headers()
            with file_path.open("rb") as f:
                self.wfile.write(f.read())
        elif path.startswith("/api/create"):
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["1"])[0])
            filename = query.get("filename", [""])[0]
            if not filename:
                self.send_json({"ok": False, "error": "Missing filename"})
                return

            token = str(uuid.uuid4())[:8]
            data = load_data()
            data[token] = {"filename": filename, "limit": limit, "opens": 0}
            save_data(data)
            self.send_json({"ok": True, "link": f"http://127.0.0.1:3000/download/{token}"})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/upload":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        if not body:
            self.send_json({"ok": False, "error": "No file uploaded"})
            return

        try:
            import cgi
            from io import BytesIO

            form = cgi.FieldStorage(
                fp=BytesIO(body),
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers.get('Content-Type', '')}
            )
            if 'file' not in form:
                self.send_json({"ok": False, "error": "No file field"})
                return

            upload = form['file']
            filename = os.path.basename(upload.filename)
            path = UPLOAD_DIR / filename
            with path.open("wb") as f:
                f.write(upload.file.read())

            self.send_json({"ok": True, "filename": filename})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def send_file(self, filename):
        path = BASE_DIR / filename
        if not path.exists():
            self.send_error(404, "Not Found")
            return
        self.send_response(200)
        if filename.endswith(".html"):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif filename.endswith(".css"):
            self.send_header("Content-Type", "text/css; charset=utf-8")
        elif filename.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.end_headers()
        with path.open("rb") as f:
            self.wfile.write(f.read())

    def send_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 3000), Handler)
    print("Server running on http://127.0.0.1:3000")
    server.serve_forever()
