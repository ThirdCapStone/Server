import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from crawler.theater import *
from db.models.theater import *
from db.connection import db_connection


def process_async(conn):
    cities = TheaterCrawler.get_city_list()
    for c_idx in range(len(cities)):
        gus = TheaterCrawler.get_gu_list(cities[c_idx]["cd"])
        Theater.insert_city_info(conn, cities[c_idx]["cd"], cities[c_idx]["cdNm"])
        
        for g_idx in range(len(gus)):
            theaters = TheaterCrawler.get_theater_list(gus[g_idx]["cd"])
            Theater.insert_gu_info(conn, gus[g_idx]["cd"], gus[g_idx]["cdNm"], cities[c_idx]["cd"])
            for theater in theaters:
                if theater['info'] != '':
                    theater["info"]["place_name"] = theater["info"]["place_name"].replace("\\", "")
                    theater["info"]["address"] = theater["info"]["address"].replace("\\", "")
                    theater["info"]["road_address"] = theater["info"]["road_address"].replace("\\", "")
                    theater["info"]["lat"] = theater["info"]["lat"].replace("\\", "")
                    theater["info"]["long"] = theater["info"]["long"].replace("\\", "")
                    Theater.insert_theater_info(conn, theater["cd"], theater["info"]["place_name"], theater["info"]["address"], theater["info"]["road_address"], theater["info"]["lat"], theater["info"]["long"], gus[g_idx]["cd"])            
                
                else:
                    Theater.insert_theater_info(conn, theater["cd"], None, None, None, None, None, gus[g_idx]["cd"])
                
def run_crawler():
    conn = db_connection()
    process_async(conn)
    conn.close()
    