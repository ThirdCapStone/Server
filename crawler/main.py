import os, sys
import time
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from crawler.models import *

#     for g_idx in range(len(gus)):
#         theaters = TheaterCrawler.get_theater_list(gus[g_idx]["cd"], cities[c_idx]["cd"])
#         for theater in theaters:
#             print(TheaterCrawler.get_coordinate(f'{cities[c_idx]["cdNm"]} {gus[g_idx]["cdNm"]} {theater["cdNm"]}', 35.146792520790235, 126.92216393293315))


async def process_async():
    start_time = time.time()
    cities = await TheaterCrawler.get_city_list()
    for c_idx in range(len(cities)):
        gus = await TheaterCrawler.get_gu_list(cities[c_idx]["cd"])

        for g_idx in range(len(gus)):
            theaters = await TheaterCrawler.get_theater_list(gus[g_idx]["cd"])
            gus[g_idx] = theaters
        
        cities[c_idx]["gu"] = list(filter(lambda x: x != [], gus))

        print(cities)
    print(time.time()-start_time)
    cities=list(filter(None, cities))
    

if __name__ == '__main__':
    asyncio.run(process_async())
    print("done")