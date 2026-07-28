from typing import Annotated, Literal

import dbm
import hashlib
from fastapi import FastAPI, Query, Depends, HTTPException
from pydantic import BaseModel, Field, BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from starlette.responses import RedirectResponse



SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
app = FastAPI()
URL_DB = "urls.db"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

fake_user_db = {
    "johndoe":{
        "username": "johndoe",
        "email": "",
        "full_name": "",
        "disabled": True,
        "hashed_password": "fakehashedsecret"
    }
}

def fake_hash_password(password: str):
    return "fakehashed" + password

def verify_password(plain_password, hashed_password):
    return hashed_password.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

class FilterParams(BaseModel):
    limit: int = Field(100, gt =0, le = 100)
    offset: int = Field(0, ge = 0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

class PostItem(BaseModel):
    original_url: str

class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None






def fake_decode_token(token):
    user = get_user(fake_user_db, token)
    return user




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

async def get_current_user(token: Annotated[set, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/token/")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_user_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/user/me")
async def read_users_me(current_user: Annotated[str, Depends(get_current_user)]):
    return current_user