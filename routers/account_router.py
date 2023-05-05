from fastapi.security.api_key import APIKeyHeader
from fastapi import Depends, APIRouter, status
from fastapi.responses import JSONResponse
from db.connection import db_connection
from fastapi.requests import Request
from db.models.account import *
from auth import auth


account_router = APIRouter(
    prefix="/account",
    tags=["account"],
)

conn = db_connection()

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
    result = Account.signup(conn, id, password, nickname, email, phone)

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

    result, account = Account.load_account(conn, id=model.id)
    if result == AccountResult.SUCCESS:
        result = account.check_session(request.session)

        if result == AccountResult.SUCCESS:

            if hashlib.sha256((model.id + account.password).encode()).hexdigest() == request.session[f"{model.id}_check_login"] and bcrypt.checkpw(model.password.encode("utf-8"), account.password.encode("utf-8")):
                result = account.signout(conn, request)

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
    result = Account.login(conn, id, password, request)

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

    result, account = Account.load_account(conn, id=id)
    if result == AccountResult.SUCCESS:
        result = account.logout(request)
    
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

    result, account = Account.load_account(conn, id=id)
    if result == AccountResult.SUCCESS:
        result = account.check_session(request.session)
        
        if result == AccountResult.SUCCESS:
            result = account.update_column(conn, password, nickname, email, phone)
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
        result, account = Account.load_account(conn, id=id)

        if result == AccountResult.SUCCESS:
            result = account.check_session(request)

            if result == AccountResult.SUCCESS:
                result = account.update_category(conn, is_add, category_num)

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
    result = Account.check_exist_column(conn, id, nickname)

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
    
    result, account = Account.load_account(conn, account_seq=account_seq, id=id)
    return JSONResponse(response_dict[result], status_code=result.value)
