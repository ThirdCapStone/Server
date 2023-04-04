from httpx import AsyncClient
from db.connection import db_connection
from db.models.account import Account
from fastapi import status
from main import app
import datetime
import pytest
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


conn = db_connection()


@pytest.mark.asyncio
async def test_signup():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:3000") as ac:
        body = {
            "id": "test_id",
            "password": "test_password",
            "nickname": "test_nickname",
            "birthday": datetime.datetime.now().date().isoformat(),
            "email": "test_email",
            "phone": "000-0000-0000"
        }

        response = await ac.put("/account/signup", data=json.dumps(body))

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:3000") as ac:
        body = {
            "id": "test_id",
            "password": "test_password2"
        }
        response = await ac.post("/account/login", data=json.dumps(body))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["id"] = "test_id2"
        response = await ac.post("/account/login", data=json.dumps(body))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["password"] = "test_password"
        response = await ac.post("/account/login", data=json.dumps(body))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["id"] = "test_id"
        response = await ac.post("/account/login", data=json.dumps(body))

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:3000") as ac:
        login_body = {
            "id": "test_id",
            "password": "test_password"
        }

        await ac.post("/account/login", data=json.dumps(login_body))

        body = {
            "nickname": "test_nickname2"
        }

        if Account.check_exist_column(conn, nickname=body["nickname"]) == status.HTTP_200_OK:
            response = await ac.patch("/account/update", data=json.dumps(body))
            _, account = Account.load_account(conn, id=login_body["id"])
            assert response.status_code == status.HTTP_200_OK and account.nickname == "test_nickname2"

        body = {
            "nickname": "admin"
        }

        if Account.check_exist_column(conn, nickname=body["nickname"]) == status.HTTP_200_OK:
            response = await ac.patch("/account/update", data=json.dumps(body))
            _, account = Account.load_account(conn, id=login_body["id"])
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_signout():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:3000") as ac:
        body = {
            "id": "test_id",
            "password": "test_password"
        }

        await ac.post("/account/login", data=json.dumps(body))

        body["password"] = "wrong_password"

        response = await ac.post("/account/signout", data=json.dumps(body))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        body["password"] = "test_password"

        response = await ac.post("/account/signout", data=json.dumps(body))

        assert response.status_code == status.HTTP_200_OK
