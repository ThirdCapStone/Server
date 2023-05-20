import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from crawler.models import *

cities = TheaterCrawler.get_city_list()
for c_idx in range(len(cities)):
    gus = TheaterCrawler.get_gu_list(cities[c_idx]["cd"])
    for g_idx in range(len(gus)):
        theaters = TheaterCrawler.get_theater_list(gus[g_idx]["cd"], cities[c_idx]["cd"])
        for theater in theaters:
            print(TheaterCrawler.get_coordinate(f'{cities[c_idx]["cdNm"]} {gus[g_idx]["cdNm"]} {theater["cdNm"]}', 35.146792520790235, 126.92216393293315))