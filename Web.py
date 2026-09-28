# 创建socket -> 绑定端口 -> 监听 -> 接收请求 -> 解析请求 -> 构造响应 -> 发送响应

import socket

def run():
    # 创建套接字
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# 地址族为IPv4，类型为TCP
    # 设置端口复用，避免端口被占用
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 ) #允许端口复用
    server.bind(('localhost', 8080)) # 绑定地址和端口
    server.listen() #开始监听
    print("Listening...")

    while True:
        # 接收请求
        conn, addr = server.accept()
        data = conn.recv(1024).decode("utf-8")
        print("原始请求：\n", data)

        body = "Hello World"
        response = (
            "HTTP/1.1 200 OK\n"
            "Content-Type: text/html; charset=utf-8\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            "\r\n"
            f"{body}"
        )
        conn.sendall(response.encode("utf-8"))
        conn.close()
run()