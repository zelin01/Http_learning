from fastapi import FastAPI,Request

app = FastAPI()

@app.get("/")
async def run_state():
    return {"程序状态": "良好"}

@app.get("/resources/path/{file}")
@app.post("/resources/path/{file}")
@app.put("/resources/path/{file}")
@app.delete("/resources/path/{file}")
async def http_url(*, request: Request, key1, key2):
    response = {
        "协议名称": request.url.scheme,
        "主机名": request.url.hostname,
        "端口": request.url.port,
        "资源路径": request.url.path,
        "参数": request.url.query,
        "KEY1 的值": key1,
        "KEY2 的值": key2,
        "请求头部": request.headers,
        "请求体": await request.body(),
    }
    return response