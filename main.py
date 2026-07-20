import sys
from urllib.request import Request

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


app = FastAPI(
    debug = True
)


class Site(BaseModel):
    name: str = "FastAPI 开发与部署"
    address: str

page = {
    "title":"这是一篇文章"
    "body""这是文章的具体内容"
}
@app.get("/post")
async def post(request: Request):
    date = {
        "site"
    }
    return {"message": "Hello World"}
@app.get("/items/{item_id}")
async def user_name():
    return {"item_id": 1}
