from fastapi.responses import JSONResponse
from fastapi import APIRouter, status
from db.models.account import *
from db.connection import db_connection
from fastapi.requests import Request

account_router = APIRouter(
    prefix = "/account",
    tags = ["account"],
)

conn = db_connection()

@account_router.put(
    "/signup",
    responses = {
        201: {
            "content": {
                "application/json": {
                    "example": {"status": "회원가입에 성공하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status": "회원가입에 실패하였습니다."}
                }
            }
        },
    }, 
)
async def signup(model: SignUpModel) -> JSONResponse:
    id = model.id
    password = model.password
    nickname = model.nickname
    birthday = model.birthday
    email = model.email
    phone = model.phone
    result = Account.signup(conn, id, password, nickname, birthday, email, phone)
    return {
        AccountResult.SUCCESS: JSONResponse({"status": "회원가입에 성공하였습니다!"}, status_code = status.HTTP_201_CREATED),
        AccountResult.FAIL: JSONResponse({"status": "회원가입에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
        AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
        AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
    } [result]


@account_router.delete(
    "/signout",
    responses = {
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "성공적으로 회원이 탈퇴되었습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status": "회원탈퇴에 실패하였습니다."}
                }
            }
        },
    }, 
)
async def signout(request: Request, id: str, password: str) -> JSONResponse:
    load_result, account = Account.load_account(conn, id = id)
    if load_result == AccountResult.SUCCESS:
        session_result = account.check_session(request)
        if session_result == AccountResult.SUCCESS:
            if hashlib.sha256((id + account.password).encode()).hexdigest() == request.session[f"{id}_check_login"] and bcrypt.checkpw(password.encode("utf-8"), account.password.encode("utf-8")):
                result = account.signout(conn, request)
                del request.session[f"{id}_check_login"]
                
                return {
                    AccountResult.SUCCESS: JSONResponse({"status": "성공적으로 회원이 탈퇴되었습니다!"}, status_code = status.HTTP_200_OK),
                    AccountResult.FAIL: JSONResponse({"status": "회원탈퇴에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
                    AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
                } [result]
                
            else:
                return JSONResponse({"status": "회원탈퇴에 실패하였습니다.", "message": "비밀번호가 일치하지 않음"}, status_code = status.HTTP_401_UNAUTHORIZED)
        
        else:
            return {
                AccountResult.FAIL: JSONResponse({"status": "회원탈퇴에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
                AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
                AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
            } [session_result]
    
    else:
        return {
            AccountResult.FAIL: JSONResponse({"status": "회원탈퇴에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
            AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
            AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
        } [load_result]

@account_router.post(
    "/login",
    responses = {
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "로그인에 성공하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status": "로그인에 실패하였습니다."}
                }
            }
        },
    }, 
)
async def login(request: Request, model: LoginModel) -> JSONResponse:
    id = model.id
    password = model.password
    
    result = Account.login(conn, id, password)
    
    if result == AccountResult.SUCCESS:
        load_result, account = Account.load_account(conn, id = id)
        if load_result == AccountResult.SUCCESS:
            request.session[f"{id}_check_login"] = hashlib.sha256((id + account.password).encode()).hexdigest()
            
            return JSONResponse({"status": "로그인에 성공하였습니다!"}, status_code = status.HTTP_200_OK)
        
        else:
            return {
                AccountResult.FAIL: JSONResponse({"status": "로그인에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
                AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
                AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
            } [load_result]
        
    return {
        AccountResult.SUCCESS: JSONResponse({"status": "로그인에 성공하였습니다!"}, status_code = status.HTTP_200_OK),
        AccountResult.FAIL: JSONResponse({"status": "로그인에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
        AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
        AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
    } [result]

    
@account_router.patch(
    "/update",
    responses = {
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "정보를 수정하였습니다!"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status": "정보 수정에 실패하였습니다."}
                }
            }
        },
        409: {
            "content": {
                "application/json": {
                    "example": {"status": "해당 닉네임이 존재합니다."}
                }
            }
        },
    }, 
)
async def update(request: Request, model: UpdateModel) -> JSONResponse:
    result, account = Account.load_account(conn, id = model.id)
    if result == AccountResult.SUCCESS:
        session_result = account.check_session(request)
        
        if session_result == AccountResult.SUCCESS:
            model.id = None
            model = dict(model)
            
            for key, value in dict(model).items():
                if value != None:
                    exec(f"result = account.update_column(conn, {key}='{value}')")
                    if result != AccountResult.SUCCESS:
                        return {
                            AccountResult.FAIL: JSONResponse({"status": "정보 수정에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
                            AccountResult.CONFLICT: JSONResponse({"status": "해당 닉네임이 존재합니다."}, status_code = status.HTTP_409_CONFLICT),
                            AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
                        } [result]
                    
            conn.commit()
            return JSONResponse({"status": "정보를 수정하였습니다!"}, status_code = status.HTTP_200_OK)
                    
                    
            
        return {
            AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
            AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
        } [session_result]
    
    return {
        AccountResult.FAIL: JSONResponse({"status": "정보 수정에 실패하였습니다."}, status_code = status.HTTP_401_UNAUTHORIZED),
        AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
        AccountResult.CONFLICT: JSONResponse({"status": "해당 닉네임이 존재합니다."}, status_code = status.HTTP_409_CONFLICT),
        AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
    } [result]
    
    
@account_router.post(
    "/check",
    responses = {
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "존재하지 않습니다!"}
                }
            }
        },
        409: {
            "content": {
                "application/json": {
                    "example": {"status": "존재합니다."}
                }
            }
        }
    }, 
)
async def check(id: Optional[str] = None, nickname: Optional[str] = None) -> JSONResponse:
    result = Account.check_exist_column(conn, id, nickname)
    
    return {
        AccountResult.SUCCESS: JSONResponse({"status": "존재하지 않습니다!"}, status_code = status.HTTP_200_OK),
        AccountResult.SESSIONTIMEOUT: JSONResponse({"status": "세션이 만료되었습니다."}, status_code = status.HTTP_408_REQUEST_TIMEOUT),
        AccountResult.CONFLICT: JSONResponse({"status": "존재합니다."}, status_code = status.HTTP_409_CONFLICT),
        AccountResult.INTERNAL_SERVER_ERROR: JSONResponse({"status": "서버 내부 에러가 발생하였습니다."}, status_code = status.HTTP_500_INTERNAL_SERVER_ERROR) 
    } [result]
    