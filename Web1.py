import socket
from urllib.parse import urlparse, parse_qs

class Request:
    def __init__(self, raw: str):
        head, _, body = raw.partition("\r\n\r\n")
        lines = head.split("\r\n")
        method, target, _ = lines[0].split(" ")
        parsed = urlparse(target)

        self.method = method
        self.path = parsed.path
        self.query = parse_qs(parsed.query)
        self.body = body
        self.headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                self.headers[k.strip().lower()] = v.strip()

class Response:
    STATUS = {200:"ok", 404:"Not Found", 500:"Internal Server Error"}
    def __init__(self, body="", status = 200, content_type = "text/html; charset = utf-8"):
        self.body = body
        self.status = status
        self.content_type = content_type

    def to_bytes(self) -> bytes:
        body_bytes = self.body.encode("utf-8")
        status_text = self.STATUS.get(self.status, "OK")
        headers = (
            f"HTTP/1.1 {self.status} {status_text}\r\n"
            f"Content-Type: {self.content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        return headers.encode("utf-8") + body_bytes

class App:
    def __init__(self):
        self.routes = {}

    def route(self, path, method = "GET"):
        def decorator(func):
            self.routes[(path, method)] = func
            return func
        return decorator
    def handle(self, raw_request: str) -> bytes:
        try:
            req = Request(raw_request)
            handler = self.routes.get((req.path, req.method))
            if handler is None:
                return Response("<h1> 404 Not Found</h1>", status = 404).to_bytes()

            result = handler(req)
            if isinstance(result, Response):
                return result.to_bytes()
            return Response(str(result)).to_bytes()
        except Exception as e:
            return Response(f"<h1> 500 {e} </h1>", status = 500).to_bytes()
    def run(self, host="127.0.0.1", port = 8000):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        print(f"* Serving on http://{host}:{port}")

        while True:
            # 接收请求
            conn, _ = server.accept()
            with conn:
                raw = conn.recv(65536).decode("utf-8")
                if not raw:
                    continue
                conn.sendall(self.handle(raw))

app = App()

@app.route("/")
def index(req):
    return "<h1> shouye </h1><a href='/hello?name=python'>去打招呼</a>"
@app.route("/hello")
def hello(req):
    name = req.query.get("name",["world"])[0]
    return f"<h1> hello {name} </h1>"

if __name__ == "__main__":
    app.run()