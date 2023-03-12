from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi
from db.connection import db_connection
from fastapi import FastAPI
from db.settings import setting
from db.models.account import *
from routers.account_router import account_router
import uvicorn


def custom_openapi():
    if not app.openapi_schema:
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        for _, method_item in app.openapi_schema.get('paths').items():
            for _, param in method_item.items():
                if param['summary'] == 'Signup':
                    del param['responses']['200']
                    
                responses = param.get('responses')
                if '422' in responses:
                    del responses['422']
                    
                if '408' not in responses:
                    responses['408'] = {
                        "description": "Request Time Out",
                        "content": {
                            "application/json": {
                                "example" : {"status": "세션이 만료되었습니다."}
                            }
                        }
                    }
                    
                if '500' not in responses:
                    responses['500'] = {
                        "description": "Internal Server Error",
                        "content": {
                            "application/json": {
                                "example": {"status": "서버 내부 에러가 발생하였습니다."}
                            }
                        }
                    }
                    
    return app.openapi_schema
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key = open("session_secret_key.txt", "r").readline())
app.include_router(account_router)
app.openapi = custom_openapi

conn = db_connection()
setting(conn)
conn.close()


if __name__ == "__main__":
    uvicorn.run(
        host = "localhost",
        app = "main:app",
        reload = True,
        port = 8080,
    )