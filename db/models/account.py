from db.models.category import Category, CategoryResult
from typing import Tuple, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request
from enum import Enum
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.message import EmailMessage
import base64
import traceback
import pymysql
import hashlib
import bcrypt
import json
import os.path

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
    

class UpdatePasswordModel(BaseModel):
    id: str
    new_password: str
    

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
                    conn.commit()
                    return AccountResult.CREATED
            
            return AccountResult.FAIL
        
        except pymysql.err.IntegrityError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.CONFLICT

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        finally:
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
    def forgot_password(conn: pymysql.connections.Connection, id: str, new_password: str, request: Request) -> AccountResult:
        cursor = conn.cursor()
        try:
            result, account = Account.load_account(conn, id=id)
            if result == AccountResult.SUCCESS:
                cursor.execute(f"""
                    UPDATE account SET password_date='{datetime.now()}', password='{bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}' WHERE id='{account.id}';
                """)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return AccountResult.SUCCESS
                
                else:
                    return AccountResult.FAIL
                    
            return result
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR

        finally:
            cursor.close()


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
    
    
    @staticmethod
    def gmail_authenticate():
        try:
            SCOPES = ['https://mail.google.com/']
            CURR_DIR = os.path.dirname(os.path.realpath(__file__))
            creds = Credentials.from_authorized_user_file(f'{CURR_DIR}/credentials.json', SCOPES)
            return (AccountResult.SUCCESS, build('gmail', 'v1', credentials=creds))

        except FileNotFoundError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (AccountResult.FAIL, None)
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (AccountResult.INTERNAL_SERVER_ERROR, None)
    
    
    @staticmethod
    def create_message(sender: str, to: str, verify_code: int):
        try:
            message = EmailMessage()
            message["From"] = sender
            message["To"] = to
            message["Subject"] = "무비스컴바인 인증 코드"
            message.set_content(f"""
                인증 코드: {verify_code}
                인증코드를 입력해주세요.
                이용해 주셔서 감사합니다.
            """)
            
            return (AccountResult.SUCCESS, {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')})
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (AccountResult.INTERNAL_SERVER_ERROR, None)


    @staticmethod
    def send_message(service, email: str, message: dict[str, str]):
        try:
            message = service.users().messages().send(userId=email, body=message).execute()
            return AccountResult.SUCCESS
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR


    @staticmethod
    def send_email(email : str, verify_code: int):
        try:
            response, service = Account.gmail_authenticate()
            if response == AccountResult.SUCCESS:
                response, message = Account.create_message("moviescombine@gmail.com", email, verify_code)
                if response == AccountResult.SUCCESS:
                    response = Account.send_message(service, "moviescombine@gmail.com", message)
                    return response
                    
            return response
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR
        
        
    @staticmethod
    def clear_email(request: Request, email: str, verify_code: int):
        try:
            if f"{email}_check_email" in request.session.keys():
                if request.session[f"{email}_check_email"] == str(verify_code):
                    del request.session[f"{email}_check_email"]
                    return AccountResult.SUCCESS

                del request.session[f"{email}_check_email"]
            return AccountResult.FAIL
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return AccountResult.INTERNAL_SERVER_ERROR


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
