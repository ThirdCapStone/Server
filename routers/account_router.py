from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from db.connection import db_connection
from fastapi import Depends, APIRouter
from fastapi.requests import Request
from db.models.account import *
from fastapi import FastAPI
from auth import auth
import random

app = FastAPI()

account_router = APIRouter(
    prefix="/account",
    tags=["account"],
)

@account_router.put(
    "/signup",
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {"message": "회원가입에 성공하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "회원가입에 실패하였습니다."}
                }
            }  
        },
        409: {  
            "content": {
                "application/json": {
                    "example": {"message": "정보가 중복됩니다."}
                }
            }
        },
    },
)
async def signup(model: SignUpModel) -> JSONResponse:
    response_dict = {
        AccountResult.CREATED: "회원가입에 성공하였습니다.",
        AccountResult.FAIL: "회원가입에 실패하였습니다.",
        AccountResult.CONFLICT: "정보가 중복됩니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    id = model.id
    password = model.password
    nickname = model.nickname
    email = model.email
    phone = model.phone
    result = Account.signup(db_connection(), id, password, nickname, email, phone)

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/signout",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "성공적으로 회원이 탈퇴되었습니다."}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "회원탈퇴에 실패하였습니다."}
                }
            }
        },
        408: {
            "content": {
                "application/json": {
                    "example": {"message": "세션이 만료되었습니다."},
                }
            }
        }
    },
)
async def signout(request: Request, model: LoginModel) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "성공적으로 회원이 탈퇴되었습니다.",
        AccountResult.FAIL: "회원탈퇴에 실패하였습니다.",
        AccountResult.SESSION_TIME_OUT: "세션이 만료되었습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result, account = Account.load_account(db_connection(), id=model.id)
    if result == AccountResult.SUCCESS:
        result = account.check_session(request.session)

        if result == AccountResult.SUCCESS:

            if hashlib.sha256((model.id + account.password).encode()).hexdigest() == request.session[f"{model.id}_check_login"] and bcrypt.checkpw(model.password.encode("utf-8"), account.password.encode("utf-8")):
                result = account.signout(db_connection(), request)

            else:
                result = AccountResult.FAIL

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/login",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "로그인에 성공하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "로그인에 실패하였습니다."}
                }
            }
        },
    },
)
async def login(request: Request, model: LoginModel) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "로그인에 성공하였습니다.",
        AccountResult.FAIL: "로그인에 실패하였습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    id = model.id
    password = model.password
    result = Account.login(db_connection(), id, password, request)

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/logout",
    responses = {
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "로그아웃에 성공하였습니다!"}
                }
            }
        },
        409: {
            "content": {
                "application/json": {
                    "example": {"message": "세션이 만료되었습니다."}
                }
            }
        },
    }
)
async def logout(request: Request, id: str) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "로그아웃에 성공하였습니다.",
        AccountResult.SESSION_TIME_OUT: "세션이 만료되었습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result, account = Account.load_account(db_connection(), id=id)
    if result == AccountResult.SUCCESS:
        result = account.logout(request)
    
    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.patch(
    "/update/password",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "정보를 수정하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "정보 수정에 실패하였습니다."}
                }
            }
        },
    }
)
async def update_password(id: str, new_password: str) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "정보를 수정하였습니다.",
        AccountResult.FAIL: "정보 수정에 실패하였습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    result = Account.forgot_password(db_connection(), id ,new_password)
    print(result)
    
    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.patch(
    "/update",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "정보를 수정하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "정보 수정에 실패하였습니다."}
                }
            }
        },
        408: {
            "content": {
                "application/json": {
                    "example": {"message": "세션이 만료되었습니다."}
                }
            }
        },
        409: {
            "content": {
                "application/json": {
                    "example": {"message": "해당 닉네임이 존재합니다."}
                }
            }
        },
    },
)
async def update(request: Request, id: str, password: Optional[str] = None, nickname: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "정보를 수정하였습니다.",
        AccountResult.FAIL: "정보 수정에 실패하였습니다.",
        AccountResult.SESSION_TIME_OUT: "세션이 만료되었습니다.",
        AccountResult.CONFLICT: "해당 닉네임이 존재합니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result, account = Account.load_account(db_connection(), id=id)
    if result == AccountResult.SUCCESS:
        result = account.check_session(request.session)
        
        if result == AccountResult.SUCCESS:
            result = account.update_column(db_connection(), password, nickname, email, phone)
            request.session[f"{id}_check_login"] = hashlib.sha256((id + account.password).encode()).hexdigest()

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.patch(
    "/update/category",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "정보를 수정하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "카테고리가 존재하지 않습니다."}
                }
            }
        },
        408: {
            "content": {
                "application/json": {
                    "example": {"message": "세션이 만료되었습니다."}
                }
            }
        }
    }
)
async def update_category(request: Request, category_num: int, is_add: bool) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "정보를 수정하였습니다.",
        AccountResult.FAIL: "카테고리가 존재하지 않습니다.",
        AccountResult.SESSION_TIME_OUT: "세션이 만료되었습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result, id = Account.session_to_account_id(request)
    if result == AccountResult.SUCCESS:
        result, account = Account.load_account(db_connection(), id=id)

        if result == AccountResult.SUCCESS:
            result = account.check_session(request)

            if result == AccountResult.SUCCESS:
                result = account.update_category(db_connection(), is_add, category_num)

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/check",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "존재하지 않습니다."}
                }
            }
        },
        409: {
            "content": {
                "application/json": {
                    "example": {"message": "존재합니다."}
                }
            }
        }
    },
)
async def check(id: Optional[str] = None, nickname: Optional[str] = None) -> JSONResponse:
    result = Account.check_exist_column(db_connection(), id, nickname)

    return JSONResponse({"message": "존재하지 않습니다." if not result else "존재합니다."}, status_code=AccountResult.SUCCESS.value if not result else AccountResult.CONFLICT.value)


@account_router.get(
    "/",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "account_seq": 63,
                        "id": "test",
                        "password": "$2b$12$wlbPZRJQPM32F7f.6JpJ9OUa7iL2gVWBmGFqsoCoNFxYYgU793FVO",
                        "nickname": "test",
                        "email": "test",
                        "phone": "test",
                        "signup_date": "2023-04-06 04:28:29",
                        "birthday": "1970-01-01",
                        "profile_image": None,
                        "password_date": "2023-04-06 04:28:30",
                        "like_categories": "[]"
                    }
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "정보를 불러오는데 실패하였습니다."}
                }
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {"message": "API 키가 유효하지 않습니다."}
                }
            }
        }
    },
    response_model_exclude_none=True
)
async def load_account(account_seq: Optional[int] = None, id: Optional[str] = None, api_key: APIKeyHeader = Depends(auth.get_api_key)) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: account.convert_json(),
        AccountResult.FAIL: {"message": "정보를 불러오는데 실패하였습니다."},
        AccountResult.FORBIDDEN: {"message": "API 키가 유효하지 않습니다."},
        AccountResult.INTERNAL_SERVER_ERROR: {"message": "서버 내부 에러가 발생하였습니다."},
    }
    
    result, account = Account.load_account(db_connection(), account_seq=account_seq, id=id)
    return JSONResponse(response_dict[result], status_code=result.value)


@account_router.post(
    "/email/send",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "이메일을 전송 했습니다."}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "이메일 전송에 실패했습니다."}
                }
            }
        },
    }
)
async def verify_email(request: Request, email: str):
    response_dict = {
        AccountResult.SUCCESS: "이메일을 전송 했습니다.",
        AccountResult.FAIL: "이메일을 전송하지 못했습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    verify_code = str(random.randint(pow(10, 5), pow(10, 6) - 1))
    request.session[f"{email}_check_email"] = verify_code
    result = Account.send_email(email, verify_code)
    
    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/eamil/cancel",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "이메일 인증에 성공하였습니다."}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"message": "이메일 인증에 실패하였습니다."}
                }
            }
        },
    }
)
async def unverify_email(request: Request, email: str, verify_code: int):
    response_dict = {
        AccountResult.SUCCESS: "이메일 인증에 성공하였습니다.",
        AccountResult.FAIL: "이메일 인증에 실패하였습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생했습니다."
    }
    
    result = Account.clear_email(request, email, verify_code)

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)
