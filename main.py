import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get('/')
def index():
    return JSONResponse({"message": "Hello World"}, status_code = status.HTTP_200_OK)

if __name__ == "__main__":
    uvicorn.run(
        host = "localhost",
        app = "main:app",
        reload = True,
        port = 3000,
    )