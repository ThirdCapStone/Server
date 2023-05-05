from db.models.category import Category, CategoryResult
from typing import Tuple, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request
from enum import Enum
import traceback
import pymysql
import hashlib
import bcrypt
import json

def json_default(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError('not JSON serializable')


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
    email: str
    phone: str


class LoginModel(BaseModel):
    id: str
    password: str
    

class Account(BaseModel):
    account_seq: int
    id: str
    password: str
    nickname: str
    email: str
    phone: str
    signup_date: datetime
    birthday: Optional[datetime]
    profile_image: Optional[str] = None
    password_date: datetime
    like_categories: str


    def __init__(self, result_tuple: Tuple[int, str, str, str, str, str, Optional[datetime], Optional[datetime], Optional[str], datetime, str]) -> None:
        super().__init__(
            account_seq=result_tuple[0],
            id=result_tuple[1],
            password=result_tuple[2],
            nickname=result_tuple[3],
            email=result_tuple[4],
            phone=result_tuple[5],
            signup_date=result_tuple[6],
            birthday=None if result_tuple[7] == None else result_tuple[7],
            profile_image=result_tuple[8],
            password_date=result_tuple[9],
            like_categories=result_tuple[10],
        )


    def convert_json(self):
        return json.loads(json.dumps(self.__dict__, default=json_default))


    @staticmethod
    def load_account(conn: pymysql.connections.Connection, account_seq: Optional[int] = None, id: Optional[str] = None) -> Tuple[AccountResult, Optional["Account"]]:
        cursor = conn.cursor()
        try:
            op = f"account_seq = {account_seq}" if account_seq != None else f"id = '{id}'"
            cursor.execute(f"""
                SELECT * FROM account WHERE {op};
            """)

            account_result = cursor.fetchall()
            if account_result == ():
                return (AccountResult.FAIL, None)

            return (AccountResult.SUCCESS, Account(account_result[0]))

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (AccountResult.INTERNAL_SERVER_ERROR, None)
        
        finally:
            cursor.close()


    @staticmethod
    def signup(conn: pymysql.connections.Connection, id: str, password: str, nickname: str, email: str, phone: str) -> AccountResult:
        cursor = conn.cursor()
        try:
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            if not Account.check_exist_column(conn, id=id) or not Account.check_exist_column(conn, nickname=nickname): 
                cursor.execute(f"""
                    INSERT INTO account(id, password, nickname, email, phone,  password_date) VALUES ('{id}', '{hashed_password}', '{nickname}', '{email}', '{phone}', '{datetime.now()}');
                """)
                if cursor.rowcount > 0:
                    return AccountResult.CREATED
            
            return AccountResult.FAIL
        
        except pymysql.err.IntegrityError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.CONFLICT

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        finally:
            conn.commit()
            cursor.close()
            

    @staticmethod
    def login(conn: pymysql.connections.Connection, id: str, password: str, request: Request) -> AccountResult:
        try:
            result, account = Account.load_account(conn, id=id)
            if result == AccountResult.SUCCESS:
                if bcrypt.checkpw(password.encode("utf-8"), account.password.encode("utf8")):
                    request.session[f"{id}_check_login"] = hashlib.sha256((id + account.password).encode()).hexdigest()
                    return AccountResult.SUCCESS

                else:
                    return AccountResult.FAIL
            else:
                return result

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR


    @staticmethod
    def check_exist_column(conn: pymysql.connections.Connection, id: Optional[str] = None, nickname: Optional[str] = None) -> bool:
        cursor = conn.cursor()
        try:
            op = f"id = '{id}'" if id != None else f"nickname = '{nickname}'"
            cursor.execute(f"""
                SELECT * FROM account WHERE {op};            
            """)

            return cursor.rowcount != 0

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            raise Exception("Error occured")
        
        finally:
            cursor.close()


    def signout(self, conn: pymysql.connections.Connection, request: Request) -> AccountResult:
        cursor = conn.cursor()
        try:
            session_result = self.check_session(request.session)
            if session_result == AccountResult.SUCCESS:
                cursor.execute(f"""
                    DELETE FROM account WHERE account_seq = {self.account_seq};
                """)
                
                if cursor.rowcount > 0:
                    self.logout(request)
                    return AccountResult.SUCCESS
                
                else:
                    return AccountResult.FAIL

            else:
                return session_result

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        finally:
            conn.commit()
            cursor.close()
            
    
    def logout(self, request: Request) -> AccountResult:
        try:
            session = request.session
            if f"{self.id}_check_login" in session.keys():
                del session[f"{self.id}_check_login"]
                return AccountResult.SUCCESS
            
            else:
                return AccountResult.SESSION_TIME_OUT
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR 


    def update_column(self, conn: pymysql.connections.Connection, password: Optional[str] = None, nickname: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> AccountResult:
        cursor = conn.cursor()
        try:
            op = ""
            if password != None:
                op += f"password_date='{datetime.now()}', password='{bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}',"
            
            if nickname != None:
                op += f"nickname='{nickname}',"
            
            if email != None:
                op += f"email='{email}',"
                
            if op != "":
                cursor.execute(f"""
                    UPDATE account SET {op[:-1]} WHERE id='{self.id}';
                """)
            
                if cursor.rowcount > 0:
                    return AccountResult.SUCCESS
            
            else:
                return AccountResult.FAIL
        
        except pymysql.err.IntegrityError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.CONFLICT

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        finally:
            conn.commit()
            cursor.close()


    def update_category(self, conn: pymysql.connections.Connection, is_add: bool, category_num: str) -> AccountResult:
        cursor = conn.cursor()
        try:
            result, category_list = Category.load_category_list(conn)
            if result == CategoryResult.SUCCESS:
                like_categories = self.like_categories.split(", ")
                
                if is_add:
                    if category_num in list(*category_list):
                        like_categories.append(category_num)
                        
                    else:
                        result = AccountResult.FAIL
                
                else:
                    if category_num in like_categories:
                        like_categories.remove(category_num)
                    
                    else:
                        result = AccountResult.FAIL
                        
            elif result == CategoryResult.INTERNAL_SERVER_ERROR:
                result = AccountResult.INTERNAL_SERVER_ERROR

            if result != AccountResult.SUCCESS:
                return result
            
            self.like_categories = str(self.like_categories)
            cursor.execute(f"""
                UPDATE account SET like_categories='{self.like_categories}' WHERE account_seq = {self.account_seq};
            """)
            
            if cursor.rowcount > 0:
                return AccountResult.SUCCESS
            
            else:
                return AccountResult.FAIL

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        finally:
            conn.commit()
            cursor.close()


    def check_session(self, session: dict) -> AccountResult:
        try:
            if f"{self.id}_check_login" in session.keys():
                if session[f"{self.id}_check_login"] == hashlib.sha256((self.id + self.password).encode()).hexdigest():
                    return AccountResult.SUCCESS

            else:
                return AccountResult.SESSION_TIME_OUT

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR