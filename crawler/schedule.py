
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db.models.theater import Theater
from db.connection import db_connection
import datetime
import aiohttp
import asyncio
import json

class ScheduleCrawler:
    @staticmethod
    async def get_movie_schedule(session, theater_code, show_date):
        url = "https://www.kobis.or.kr/kobis/business/mast/thea/findSchedule.do"
        async with session.post(url, data={"theaCd": theater_code, "showDt": show_date}, headers={"Accept": "application/json"}) as response:
            json_data = json.loads(await response.text())
            try:
                return_dict = {"theater_seq": theater_code, "schedule": json_data["schedule"]}
                return return_dict

            except KeyError:
                print(json_data)
                return None
            
async def get_schedules():
    async with aiohttp.ClientSession() as session:
        theaters = list(map(lambda x: x[0], Theater.get_all_theater_code(db_connection())))
        tasks = []
        for theater in theaters:
            for i in range(7):
                day = (datetime.date.today() + datetime.timedelta(days = i)).strftime("%Y%m%d")
                tasks.append(ScheduleCrawler.get_movie_schedule(session, theater, day))
        result = await asyncio.gather(*tasks)
        
        return result
