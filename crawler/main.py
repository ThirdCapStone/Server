import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from crawler.models import *
from db.connection import db_connection

def main(conn: Connection):    
    result, movie_list = MovieCrawler.load_movie_list()
    for movie_id in movie_list:
        response, cast_list = MovieCrawler.load_cast_info(conn, movie_id)
        for cast in cast_list:
            response, crawl_movie_id_list = MovieCrawler.load_movie_id_from_cast(cast["person_id"])
            if crawl_movie_id_list != None:
                for crawl_movie_id in crawl_movie_id_list:
                    response, movie_data = MovieCrawler.load_movie_info(conn, crawl_movie_id)
                    print(movie_data)
                 
    #result, movie_list = MovieCrawler.load_movie_list()
    #for movie_id in movie_list:
    #    response, data = MovieCrawler.load_movie_info(conn, movie_id)
    #    print(data)
        
main(db_connection())