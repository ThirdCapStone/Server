from fastapi.responses import JSONResponse
from db.models.theater import *
from db.connection import db_connection 
from fastapi import APIRouter

theater_router = APIRouter(
    prefix="/theater",
    tags=["theater"]
)

@theater_router.get("/")
async def load_all_theater():
    cities = Theater.get_city_list(db_connection())
    for c_idx in range(len(cities)):
        gus = Theater.get_gu_list(db_connection(), cities[c_idx]["city_seq"])
        cities[c_idx]["gus"] = gus
        for g_idx in range(len(gus)):
            theaters = Theater.get_theater_list(db_connection(), gus[g_idx]["gu_seq"])
            gus[g_idx]["theaters"] = theaters
    return JSONResponse(cities)
