
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from httpx import AsyncClient
from db.connection import db_connection
from db.models.account import Account
from auth.env import API_KEY
from fastapi import status
from main import app
import pytest
import json


conn = db_connection()
BASE_URL = "http://127.0.0.1:8000/account"

@pytest.mark.asyncio
async def test_signup():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "test_username",
            "password": "test_password",
            "nickname": "test_nickname",
            "email": "test_email",
            "phone": "000-0000-0000"
        }
        
        response = await ac.put("/signup", data=json.dumps(body))
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "test_username",
            "password": "test_password2"
        }
        
        response = await ac.post("/login", data=json.dumps(body))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["id"] = "test_username2"
        response = await ac.post("/login", data=json.dumps(body))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["password"] = "test_password"
        response = await ac.post("/login", data=json.dumps(body))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["id"] = "test_username"
        response = await ac.post("/login", data=json.dumps(body))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_logout():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "test_username",
            "password": "test_password"
        }
        await ac.post("/login", data=json.dumps(body))
        
        response = await ac.post("/logout", params={"id": body["id"]})
        assert response.status_code == status.HTTP_200_OK
        
        response = await ac.patch("/update", params={"id": body["id"], "nickname": "test_nickname"})
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        

@pytest.mark.asyncio
async def test_update():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        login_body = {
            "id": "test_username",
            "password": "test_password"
        }

        await ac.post("/login", data=json.dumps(login_body))

        body = {
            "nickname": "test_nickname2"
        }

        if Account.check_exist_column(conn, nickname=body["nickname"]) == status.HTTP_200_OK:
            response = await ac.patch("/update", data=json.dumps(body))
            _, account = Account.load_account(conn, id=login_body["id"])
            assert response.status_code == status.HTTP_200_OK and account.nickname == body["nickname"]

        if Account.check_exist_column(conn, nickname=body["nickname"]) == status.HTTP_200_OK:
            response = await ac.patch("/update", data=json.dumps(body))
            _, account = Account.load_account(conn, id=login_body["id"])
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_check():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "test_username"
        }
        
        response = await ac.post("/check", params=body)
        assert response.status_code == status.HTTP_409_CONFLICT
        
        body["id"] = "test_username2"
        response = await ac.post("/check", params=body)
        assert response.status_code == status.HTTP_200_OK
        
        del body["id"]
        body["nickname"] = "test_nickname"
        response = await ac.post("/check", params=body)
        assert response.status_code == status.HTTP_409_CONFLICT
        
        body["nickname"] = "test_nickname2"
        response = await ac.post("/check", params=body)
        assert response.status_code == status.HTTP_200_OK
        

@pytest.mark.asyncio
async def test_load_account():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "tset_username"
        }
        
        response = await ac.get(f"?id={body['id']}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        

@pytest.mark.asyncio
async def test_signout():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        body = {
            "id": "test_username",
            "password": "test_password"
        }

        await ac.post("/login", data=json.dumps(body))
        
        body["password"] = "wrong_password"
        response = await ac.post("/signout", data=json.dumps(body))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["password"] = "test_password"
        response = await ac.post("/signout", data=json.dumps(body))
        assert response.status_code == status.HTTP_200_OK
