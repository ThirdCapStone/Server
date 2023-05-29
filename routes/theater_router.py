from fastapi.responses import JSONResponse
from crawler.models import TheaterCrawler
from fastapi import APIRouter
import asyncio

theater_router = APIRouter(
    prefix="/theater",
    tags=["theater"]
)

async def process_async():
    cities = await TheaterCrawler.get_city_list()
    for c_idx in range(len(cities)):
        gus = await TheaterCrawler.get_gu_list(cities[c_idx]["cd"])

        for g_idx in range(len(gus)):
            theaters = await TheaterCrawler.get_theater_list(gus[g_idx]["cd"])
            gus[g_idx] = theaters
        
        cities[c_idx]["gu"] = list(filter(lambda x: x != [], gus))
    return cities

cities = asyncio.run(process_async())

@theater_router.get("/")
async def load_all_theater():
    return JSONResponse(cities)


@theater_router.get("/{address}")
async def load_location():
    return JSONResponse({"message": "Hello World"})