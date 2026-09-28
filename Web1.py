from urllib.parse import urlparse, parse_qs

class Request:
    def __init__(self, raw: str):
        head, _, body = raw.partition("\r\n\r\n")
        lines = body.split("\r\n")
        method, target = lines[0].split(" ")

        self.method = method
        parsed = urlparse(target)
        self.path = parsed.path

        self.query = parse_qs(parsed.query)
        self.body = body

        self.headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                self.headers[k.strip().lower()] = v.strip()

class Response:
    def __init__(self, body="", status = 200, content_type = "text/html; charset = utf-8"):
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = {}

    def to_bytes(self) -> bytes:
        body_bytes = self.body.encode("utf-8")
        status_text = {200: "ok", 404: "Not Found", 500: "Internal Server Error"}.get(self.status,"ok")
        lines = [f"HTTP/1.1 {self.status} {status_text}"]
        lines.append(f"Content-Type: {self.content_type}")
        lines.append(f"Content-Length: {len(body_bytes)}")
        for k, v in self.headers.items():
            lines.append(f"{k}: {v}")
        lines.append("")
        lines.append("")
        return ("\r\n".join(lines)).encode("utf-8") + body_bytes