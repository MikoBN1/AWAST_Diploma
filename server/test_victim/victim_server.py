"""
Simple vulnerable web server for testing ZAP XSS detection.
Has reflected XSS on /xss_r endpoint — input is echoed directly into HTML.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote


class VulnerableHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/":
            self._respond(200, self._index_page())
        elif path == "/xss_r":
            name = params.get("name", [""])[0]
            self._respond(200, self._xss_reflected_page(name))
        else:
            self._respond(404, "<h1>404 Not Found</h1>")

    def _respond(self, code: int, body: str):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    @staticmethod
    def _index_page() -> str:
        return """<!DOCTYPE html>
<html>
<head><title>AWAST Test Victim</title></head>
<body>
    <h1>AWAST Vulnerable Test Server</h1>
    <ul>
        <li><a href="/xss_r">Reflected XSS</a></li>
        <li><a href="/xss_r?name=test">Reflected XSS (with param)</a></li>
    </ul>
</body>
</html>"""

    @staticmethod
    def _xss_reflected_page(name: str) -> str:
        # VULNERABLE: name is injected directly into HTML without escaping
        result = f"<p>Hello {name}</p>" if name else ""
        return f"""<!DOCTYPE html>
<html>
<head><title>XSS Reflected Test</title></head>
<body>
    <h1>Reflected XSS Test Page</h1>
    <form action="/xss_r" method="GET">
        <input type="text" name="name" placeholder="Your name">
        <button type="submit">Submit</button>
    </form>
    {result}
</body>
</html>"""


if __name__ == "__main__":
    host, port = "0.0.0.0", 9999
    server = HTTPServer((host, port), VulnerableHandler)
    print(f"[+] Victim server running on http://{host}:{port}")
    print(f"[+] XSS Reflected: http://localhost:{port}/xss_r?name=test")
    server.serve_forever()
