from typing import Annotated, Literal

import dbm
import hashlib
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
import random

from starlette.responses import RedirectResponse

app = FastAPI()
URL_DB = "urls.db"

class FilterParams(BaseModel):
    limit: int = Field(100, gt =0, le = 100)
    offset: int = Field(0, ge = 0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

class PostItem(BaseModel):
    original_url: str

@app.get("/itmes/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

@app.post("/short")
async def short_creat(url: PostItem):
    short_url = short_random(original_url=url.original_url)
    store_short_url(short_url, url.original_url)
    return {"short_url": short_url}

@app.get("/short/{short_url}")
async def short(short_key: str):
    url = get_url_by_key(short_key)
    #return{"original_url": url}
    return RedirectResponse(f'https://{url}')

def get_url_by_key(key: str):
    db = dbm.open(URL_DB, "c")
    url = db.get(key)
    db.close()
    return url

def short_random(*,original_url: str, length:int = 8):
    random_str = hashlib.md5(original_url.encode()).hexdigest()[:length]
    return random_str

def store_short_url(short_url: str, original_url: str):
    db = dbm.open(URL_DB, "c")
    db[short_url] = original_url.encode("utf-8")
    db.close()


