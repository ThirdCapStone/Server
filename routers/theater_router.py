from fastapi.responses import JSONResponse
from crawler.models import TheaterCrawler
from fastapi import APIRouter

theater_router = APIRouter(
    prefix="/theater",
    tags=["theater"]
)

cities = TheaterCrawler.get_city_list()
for c_idx in range(len(cities)):
    gus = TheaterCrawler.get_gu_list(cities[c_idx]["cd"])

    for g_idx in range(len(gus)):
        theaters = TheaterCrawler.get_theater_list(gus[g_idx]["cd"], cities[c_idx]["cd"])
        gus[g_idx] = theaters
        
    cities[c_idx]["gu"] = gus
    

@theater_router.get("/")
async def load_all_theater():
    return JSONResponse(cities)


@theater_router.get("/{address}")
async def load_location():
    return JSONResponse({"message": "Hello World"})