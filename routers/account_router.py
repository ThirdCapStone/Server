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
    },
)
async def signup(model: SignUpModel) -> JSONResponse:
    response_dict = {
        AccountResult.CREATED: "회원가입에 성공하였습니다.",
        AccountResult.FAIL: "회원가입에 실패하였습니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    id = model.id
    password = model.password
    nickname = model.nickname
    birthday = model.birthday
    email = model.email
    phone = model.phone
    result = Account.signup(
        conn, id, password, nickname, birthday, email, phone)

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
        result = account.check_session(request)

        if result == AccountResult.SUCCESS:

            if hashlib.sha256((model.id + account.password).encode()).hexdigest() == request.session[f"{model.id}_check_login"] and bcrypt.checkpw(model.password.encode("utf-8"), account.password.encode("utf-8")):
                result = account.signout(conn, request)
                del request.session[f"{model.id}_check_login"]

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
    result = Account.login(conn, id, password)

    if result == AccountResult.SUCCESS:
        result, account = Account.load_account(conn, id=id)

        if result == AccountResult.SUCCESS:
            request.session[f"{id}_check_login"] = hashlib.sha256(
                (id + account.password).encode()).hexdigest()

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
        409: {
            "content": {
                "application/json": {
                    "example": {"message": "해당 닉네임이 존재합니다."}
                }
            }
        },
    },
)
async def update(request: Request, model: UpdateModel) -> JSONResponse:
    response_dict = {
        AccountResult.SUCCESS: "정보를 수정하였습니다.",
        AccountResult.FAIL: "정보 수정에 실패하였습니다.",
        AccountResult.CONFLICT: "해당 닉네임이 존재합니다.",
        AccountResult.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result, account = Account.load_account(conn, id=model.id)
    if result == AccountResult.SUCCESS:
        result = account.check_session(request)
        print(result)

        if result == AccountResult.SUCCESS:
            for key, value in dict(model).items():
                if value != None:
                    result = eval(
                        f"account.update_column(conn, {key}='{value}')")
                    if key == "password":
                        request.session[f"{model.id}_check_login"] = hashlib.sha256(
                            (model.id + value).encode()).hexdigest()

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
async def update_category(request: Request, category: int, is_add: bool) -> JSONResponse:
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
                result = account.update_category(conn, is_add, category)

    return JSONResponse({"message": response_dict[result]}, status_code=result.value)


@account_router.post(
    "/check",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "존재하지 않습니다!"}
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
    return {
        AccountResult.SUCCESS: JSONResponse({"message": "존재하지 않습니다!"}, status_code=status.HTTP_200_OK),
        AccountResult.CONFLICT: JSONResponse({"message": "존재합니다."}, status_code=status.HTTP_409_CONFLICT),
        AccountResult.INTERNAL_SERVER_ERROR: JSONResponse(
            {"message": "서버 내부 에러가 발생하였습니다."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    }[Account.check_exist_column(conn, id, nickname)]


@account_router.get(
    "/"
)
async def load_account(account_seq: Optional[int] = None, id: Optional[str] = None, api_key: APIKeyHeader = Depends(auth.get_api_key)) -> JSONResponse:
    result, account = Account.load_account(
        conn, account_seq=account_seq, id=id)
    if result == AccountResult.SUCCESS:
        return JSONResponse(vars(account), status_code=status.HTTP_200_OK)

    match result:
        case AccountResult.FAIL:
            pass
        case AccountResult.FORBIDDEN:
            pass
        case AccountResult.INTERNAL_SERVER_ERROR:
            pass
        case _:
            pass
