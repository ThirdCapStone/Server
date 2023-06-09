from fastapi import APIRouter
from crawler.schedule import get_schedules
import asyncio

schedule_router = APIRouter(
    prefix="/schedule",
    tags=["schedule"]
)

schedules = asyncio.run(get_schedules())

@schedule_router.get("/")
async def get_all_schedules():
    return schedules


@schedule_router.get("/{theater_cd}")
async def get_schedules_with_theater_seq(theater_cd: int):
    return filter(lambda x: x["theater_seq"] == theater_cd, schedules)