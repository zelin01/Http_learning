import socket

def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    server.bind(('localhost', 8080))
    server.listen()
    print("Listening...")

    while True:
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