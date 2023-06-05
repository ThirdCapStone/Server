from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routes.account_router import account_router
from routes.theater_router import theater_router
from routes.movie_router import movie_router
from fastapi.openapi.utils import get_openapi
from db.connection import db_connection
from db.settings import setting
from db.models.account import *
from fastapi import FastAPI
import uvicorn

app = FastAPI()
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

                responses['500'] = {
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {"message": "서버 내부 에러가 발생하였습니다."}
                        }
                    }
                }

    return app.openapi_schema


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=open("session_secret_key.txt", "r").readline(),
)
app.include_router(account_router)
app.include_router(theater_router)
app.include_router(movie_router)
app.openapi = custom_openapi

conn = db_connection()
setting(conn)
conn.close()


if __name__ == "__main__":
    uvicorn.run(
        host="127.0.0.1",
        app="main:app",
        reload=True,
        port=8000,
    )
