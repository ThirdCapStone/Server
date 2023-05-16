from typing import Tuple, Any
from crawler.models import CrawlerResponse, MovieCrawler
from pymysql.connections import Connection
import traceback

class Movie:
    @staticmethod
    def load_movie_list(conn: Connection) -> Tuple[CrawlerResponse, Any]:
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                SELECT movie_seq FROM movie;
            """)
            
            result = cursor.fetchall()
            if result != ():
                return (CrawlerResponse.SUCCESS, result)

            else:
                return (CrawlerResponse.FAIL, None)

        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
        
        finally:
            cursor.close()
            
    
    @staticmethod
    def load_movie_info_with_movie_seq(conn: Connection, movie_seq: int) -> Tuple[CrawlerResponse, Any]:
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                SELECT * FROM movie WHERE movie_seq={movie_seq};
            """)
            
            result = cursor.fetchall()
            if result != ():
                return (CrawlerResponse.SUCCESS, result)

            else:
                return (CrawlerResponse.FAIL, None)
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
        
        finally:
            cursor.close()
