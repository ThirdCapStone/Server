from typing import List, Tuple, Union, Dict, Any, Optional
from typing_extensions import Self
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request
from datetime import date
from enum import Enum
import traceback
import pymysql
import hashlib
import bcrypt
import json


class AccountResult(Enum):
    SUCCESS = 200
    CREATED = 201
    FAIL = 401
    FORBIDDEN = 403
    SESSION_TIME_OUT = 408
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500


class SignUpModel(BaseModel):
    id: str
    password: str
    nickname: str
    birthday: date
    email: str
    phone: str


class LoginModel(BaseModel):
    id: str
    password: str


class UpdateModel(BaseModel):
    id: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def convert_json(self):
        return json.dumps(self, default=lambda x: x.__dict__)


class Account(BaseModel):
    account_seq: int
    id: str
    password: str
    nickname: str
    email: str
    phone: str
    signup_date: datetime
    birthday: date
    profile_image: Optional[str] = None
    password_date: datetime
    like_categories: Union[Optional[List[int]], Optional[str]] = None

    def __init__(self, result_tuple: Tuple[int, str, datetime, bytes]) -> None:
        super().__init__(
            account_seq=result_tuple[0],
            id=result_tuple[1],
            password=result_tuple[2],
            nickname=result_tuple[3],
            email=result_tuple[4],
            phone=result_tuple[5],
            signup_date=result_tuple[6],
            birthday=result_tuple[7],
            profile_image=None if result_tuple[8] == None else result_tuple[8].decode(
                "utf-8"),
            password_date=result_tuple[9],
            like_categories=result_tuple[10],
        )

    @staticmethod
    def load_account(conn: pymysql.connections.Connection, account_seq: Optional[int] = None, id: Optional[str] = None) -> Tuple[AccountResult, Optional[Self]]:
        try:
            cursor = conn.cursor()
            if id == None:
                cursor.execute(f"""
                    SELECT * FROM account WHERE `account_seq` = {account_seq};
                """)

            else:
                cursor.execute(f"""
                    SELECT * FROM account WHERE `id` = '{id}';
                """)

            account_result = cursor.fetchall()

            if account_result == ():
                cursor.close()
                return (AccountResult.FAIL, None)

            cursor.close()
            return (AccountResult.SUCCESS, Account(account_result[0]))

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (AccountResult.INTERNAL_SERVER_ERROR, None)

    @staticmethod
    def login(conn: pymysql.connections.Connection, id: str, password: str) -> AccountResult:
        try:
            result, account = Account.load_account(conn, id=id)
            if result == AccountResult.FAIL:
                return AccountResult.FAIL

            else:
                if bcrypt.checkpw(password.encode("utf-8"), account.password.encode("utf8")):
                    return AccountResult.SUCCESS

                else:
                    return AccountResult.FAIL

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    @staticmethod
    def check_exist_column(conn: pymysql.connections.Connection, id: Optional[str] = None, nickname: Optional[str] = None) -> AccountResult:
        try:
            cursor = conn.cursor()

            if id == None:
                cursor.execute(f"""
                    SELECT nickname FROM account WHERE nickname = '{nickname}';       
                """)

            else:
                cursor.execute(f"""
                    SELECT id FROM account WHERE id = '{id}';
                """)

            result = cursor.fetchall()
            cursor.close()

            if result == ():
                return AccountResult.SUCCESS

            else:
                return AccountResult.CONFLICT

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    @staticmethod
    def signup(conn: pymysql.connections.Connection, id: str, password: str, nickname: str, birthday: datetime, email: str, phone: str) -> AccountResult:
        try:
            cursor = conn.cursor()

            hashed_password = bcrypt.hashpw(password.encode(
                "utf-8"), bcrypt.gensalt()).decode("utf-8")

            cursor.execute(f"""
                INSERT INTO account(id, password, nickname, email, phone, birthday, password_date) VALUES ('{id}', '{hashed_password}', '{nickname}', '{email}', '{phone}', '{birthday}', '{datetime.now()}');
            """)

            conn.commit()
            cursor.close()

            return AccountResult.CREATED

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    def signout(self, conn: pymysql.connections.Connection, request: Request) -> AccountResult:
        try:
            session_result = self.check_session(request)

            if session_result == AccountResult.SUCCESS:
                cursor = conn.cursor()
                cursor.execute(f"""
                    DELETE FROM account WHERE account_seq = {self.account_seq};
                """)

                conn.commit()
                cursor.close()
                return AccountResult.SUCCESS

            else:
                return session_result

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    def update_column(self, conn: pymysql.connections.Connection, **kwargs: Dict[str, Any]) -> AccountResult:
        try:
            update_list = ["password", "nickname",
                           "email", "phone", "profile_image"]
            cursor = conn.cursor()

            for key, value in kwargs.items():
                if key in update_list:
                    if key == "password":
                        cursor.execute(f"""
                            UPDATE account SET password_date = '{datetime.now()}' WHERE id = '{self.id}';
                        """)
                        value = bcrypt.hashpw(value.encode(
                            "utf-8"), bcrypt.gensalt()).decode("utf-8")

                    cursor.execute(f"""
                        UPDATE account SET {key} = '{value}' WHERE id = '{self.id}';            
                    """)

                    if key in ("id", "nickname"):
                        flag = exec(
                            f"Account.check_exist_column(conn, {key} = '{value}')")
                        if flag == AccountResult.CONFLICT:
                            return AccountResult.CONFLICT

            conn.commit()
            cursor.close()
            return AccountResult.SUCCESS

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    def update_category(self, conn: pymysql.connections.Connection, is_add: bool, category_num: Optional[int] = None) -> AccountResult:
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT * FROM category WHERE category_seq = {category_num};            
            """)

            result = cursor.fetchall()

            if result == ():
                cursor.close()
                return AccountResult.FAIL

            else:
                if isinstance(self.like_categories, str):
                    if self.like_categories == '[]':
                        self.like_categories = list()
                    else:
                        self.like_categories = list(
                            map(int, self.like_categories.strip('][').split(', ')))

                if is_add:
                    self.like_categories.append(category_num)
                    self.like_categories = list(set(self.like_categories))

                else:
                    self.like_categories.remove(category_num)

                self.like_categories = str(self.like_categories)
                cursor.execute(f"""
                    UPDATE account SET like_categories = '{self.like_categories}' WHERE account_seq = {self.account_seq};
                """)

            conn.commit()
            cursor.close()
            return AccountResult.SUCCESS

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

    def check_session(self, request: Request) -> AccountResult:
        try:
            session = request.session

            if f"{self.id}_check_login" not in session.keys():
                return AccountResult.SESSION_TIME_OUT

            else:
                if session[f"{self.id}_check_login"] == hashlib.sha256((self.id + self.password).encode()).hexdigest():
                    return AccountResult.SUCCESS

                else:
                    return AccountResult.FAIL

        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
