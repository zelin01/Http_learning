import socket
import traceback
from urllib.parse import urlparse, parse_qs


# ============================================================
# Request：把原始的 HTTP 请求文本，解析成结构化对象
# ============================================================
class Request:
    """
    一个 HTTP 请求本质上就是一段文本，格式如下：

        GET /hello?name=python HTTP/1.1     <- 请求行（方法 + 路径 + 协议版本）
        Host: 127.0.0.1:8000                <- 请求头（若干行 key: value）
        User-Agent: curl/7.68.0
        Accept: */*
                                            <- 空行（分隔头部和请求体）
        (请求体，GET 请求通常为空)

    这个类负责把上面这段文本拆成：method / path / query / headers / body
    """

    def __init__(self, raw: str):
        # partition 按第一个 "\r\n\r\n" 把请求切成两半：
        #   head = 请求行 + 所有请求头
        #   body = 请求体（可能为空字符串）
        # 注意：HTTP 协议规定用 \r\n 作为行分隔符，头部和 body 之间有一个空行，
        #       所以这个空行实际上就是额外的 "\r\n\r\n" 里的第二个 \r\n
        head, _, body = raw.partition("\r\n\r\n")

        # 请求行和请求头都在 head 里，所以按 \r\n 拆的是 head，不是 body
        # 拆完形如：
        #   ["GET /hello?name=python HTTP/1.1",
        #    "Host: 127.0.0.1:8000",
        #    "User-Agent: curl/7.68.0",
        #    ...]
        lines = head.split("\r\n")

        # 第一行是请求行，按空格拆成三部分：
        #   method = "GET"
        #   target = "/hello?name=python"
        #   第三个是协议版本 "HTTP/1.1"，用 _ 接住（不需要）
        method, target, _ = lines[0].split(" ")

        # 把 target 拆成路径和查询参数：
        #   parsed.path  = "/hello"
        #   parsed.query = "name=python"
        parsed = urlparse(target)

        self.method = method                              # 请求方法，如 GET / POST
        self.path = parsed.path                           # 路径，如 /hello
        # parse_qs 把查询串解析成字典，值统一是列表：
        #   "name=python&tag=a&tag=b" -> {"name": ["python"], "tag": ["a", "b"]}
        self.query = parse_qs(parsed.query)
        self.body = body                                  # 请求体（GET 时为空）
        self.headers = {}                                 # 请求头字典

        # 从第二行开始都是请求头，逐行解析
        for line in lines[1:]:
            # 只处理形如 "Key: Value" 的行（空行或格式不对的跳过）
            if ":" in line:
                # split(":", 1) 只切第一个冒号，防止 value 里也含冒号（如时间戳）
                k, v = line.split(":", 1)
                # 头字段名统一转小写，方便后续大小写不敏感地读取
                self.headers[k.strip().lower()] = v.strip()


# ============================================================
# Response：把要返回的内容，拼成符合 HTTP 协议的字节流
# ============================================================
class Response:
    """
    一个 HTTP 响应本质上也是一段文本，格式如下：

        HTTP/1.1 200 OK                     <- 状态行（协议版本 + 状态码 + 原因短语）
        Content-Type: text/html; charset=utf-8   <- 响应头
        Content-Length: 13                  <- 响应体字节数，客户端靠它判断读多少
                                            <- 空行（必须有！分隔头部和 body）
        <h1>hello</h1>                      <- 响应体

    这个类负责把 body / status / content_type 拼成上面这种格式。
    """

    # 状态码 -> 原因短语 的映射，用于拼状态行
    STATUS = {200: "OK", 404: "Not Found", 500: "Internal Server Error"}

    def __init__(self, body="", status=200, content_type="text/html; charset=utf-8"):
        self.body = body                  # 响应体内容（字符串）
        self.status = status              # HTTP 状态码，如 200 / 404 / 500
        self.content_type = content_type  # 内容类型，默认 HTML + UTF-8

    def to_bytes(self) -> bytes:
        """把响应对象序列化成可以直接通过 socket 发送的字节流"""
        # 协议规定 Content-Length 是「字节数」而非「字符数」，
        # 中文一个字符占 3 字节，所以必须先 encode 再取长度
        body_bytes = self.body.encode("utf-8")

        # 根据状态码取原因短语；找不到就兜底成 "OK"
        status_text = self.STATUS.get(self.status, "OK")

        # 拼装响应头。每一行都以 \r\n 结尾（HTTP 用 CRLF，不是单纯的 \n）
        headers = (
            f"HTTP/1.1 {self.status} {status_text}\r\n"   # 状态行
            f"Content-Type: {self.content_type}\r\n"       # 告诉客户端内容类型和编码
            f"Content-Length: {len(body_bytes)}\r\n"       # 告诉客户端 body 有多少字节
            f"Connection: close\r\n"                       # 发完就关连接（简化处理）
            f"\r\n"                                        # 空行：头部结束的标志，必须有
        )

        # 头部（编码成字节） + 响应体（字节）拼在一起返回
        return headers.encode("utf-8") + body_bytes


# ============================================================
# App：框架主体，负责路由注册 + 请求分发 + 启动服务器
# ============================================================
class App:
    def __init__(self):
        # 路由表：键是 (路径, 方法)，值是处理函数
        # 例如 {("/hello", "GET"): hello, ("/", "GET"): index}
        self.routes = {}

    def route(self, path, method="GET"):
        """
        装饰器工厂。用法：

            @app.route("/hello")
            def hello(req):
                ...

        等价于：hello = app.route("/hello")(hello)
        它把 (路径, 方法) -> 函数 存进路由表，然后原样返回函数。
        """
        def decorator(func):
            self.routes[(path, method)] = func   # 登记路由
            return func                          # 返回原函数，不改变它
        return decorator

    def handle(self, raw_request: str) -> bytes:
        """
        处理一个原始请求文本，返回要发送的字节流。
        流程：解析请求 -> 查路由 -> 调处理函数 -> 包装成 Response
        """
        try:
            # 1. 解析原始请求
            req = Request(raw_request)

            # 2. 根据 (路径, 方法) 在路由表里找处理函数
            handler = self.routes.get((req.path, req.method))

            # 3. 没找到 -> 返回 404
            if handler is None:
                return Response("<h1>404 Not Found</h1>", status=404).to_bytes()

            # 4. 调用处理函数，把 Request 传进去
            result = handler(req)

            # 5. 处理函数的返回值可以是 Response 对象，也可以是普通字符串
            if isinstance(result, Response):
                return result.to_bytes()             # 已经是 Response，直接序列化
            return Response(str(result)).to_bytes()  # 否则包一层 Response

        except Exception as e:
            # 任何异常都不要让服务器崩溃，统一返回 500
            # 开发阶段打印堆栈，方便定位问题（否则异常会被吞掉，很难排查）
            traceback.print_exc()
            return Response(f"<h1>500 {e}</h1>", status=500).to_bytes()

    def run(self, host="127.0.0.1", port=8000):
        """启动服务器，进入「接受连接 -> 处理 -> 响应」的循环"""

        # 1. 创建 TCP/IPv4 套接字
        #    AF_INET    = 使用 IPv4
        #    SOCK_STREAM = 面向连接的字节流（即 TCP）
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 2. 允许端口复用。服务器重启时，上个进程的 socket 可能还在 TIME_WAIT，
        #    不开这个选项会报 "Address already in use"
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 3. 绑定地址和端口。127.0.0.1 是回环地址，只有本机能访问；
        #    想局域网访问改成 "0.0.0.0"
        server.bind((host, port))

        # 4. 进入监听模式，backlog=5 表示内核等待队列最多排 5 个连接
        server.listen(5)
        print(f"* Serving on http://{host}:{port}")

        # 5. 主循环：不断接受客户端连接
        while True:
            # accept() 是阻塞的，直到有客户端连进来才返回
            #   conn = 专门和这个客户端通信的新套接字
            #   _    = 客户端地址 (ip, port)，这里用不到
            conn, _ = server.accept()

            # with conn 确保离开代码块时自动关闭连接，异常也不会泄漏
            with conn:
                # 读取客户端发来的数据。65536 是缓冲区大小，GET 请求足够
                # decode 用 errors="ignore" 防止非法字节导致崩溃
                raw = conn.recv(65536).decode("utf-8", errors="ignore")

                # 客户端可能直接断开，收到空数据就跳过
                if not raw:
                    continue

                # 处理请求，把响应的字节流发回去
                conn.sendall(self.handle(raw))


# ============================================================
# 使用框架：注册路由 + 启动
# ============================================================
app = App()

@app.route("/")
def index(req):
    """首页：返回一个带链接的 HTML"""
    return "<h1>shouye</h1><a href='/hello?name=python'>去打招呼</a>"

@app.route("/hello")
def hello(req):
    """
    打招呼页：从查询参数里取 name，没有就用 "world"。
    req.query 的值是列表（parse_qs 的特性），所以取 [0]
    """
    name = req.query.get("name", ["world"])[0]
    return f"<h1>hello {name}</h1>"

if __name__ == "__main__":
    app.run()