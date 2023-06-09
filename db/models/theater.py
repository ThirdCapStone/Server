from pymysql.connections import Connection
from pymysql.err import IntegrityError
from typing import Optional
from enum import Enum
import traceback

class TheaterResult(Enum):
    FAIL = 0
    SUCCESS = 1
    CONFLICT = 2
    INTERNAL_SERVER_ERROR = 3


class Theater:
    @staticmethod
    def get_city_list(conn: Connection) -> Optional[any]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT city_seq, city_name FROM city;
            """)
            
            results = cursor.fetchall()
            return_list = []
            for result in results:
                return_list.append({
                    "city_seq": result[0],
                    "citt_name": result[1]
                })
            
            return return_list
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.FAIL
        
        finally:
            cursor.close()


    @staticmethod
    def get_gu_list(conn: Connection, city_seq: str):
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT gu_seq, gu_name FROM gu WHERE city_seq='{city_seq}';
            """)
            
            return_list = []
            for result in cursor.fetchall():
                return_list.append({
                    "gu_seq": result[0],
                    "gu_name": result[1],
                })
                
            return return_list
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.FAIL
        
        finally:
            cursor.close()
            
        
    @staticmethod
    def get_theater_list(conn: Connection, gu_seq: str):
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM theater WHERE gu_seq='{gu_seq}';
            """)
            
            return_list = []
            for result in cursor.fetchall():
                return_list.append({
                    "theater_seq": result[0],
                    "place_name": result[1],
                    "address": result[2],
                    "road_address": result[3],
                    "lat": result[4],
                    "long": result[5]
                })
                
            return return_list
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(TheaterResult.FAIL, e, e.__traceback__))}")
            return TheaterResult.FAIL
        
        finally:
            cursor.close()
    
    
    @staticmethod
    def get_all_theater_code(conn):
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                SELECT theater_seq FROM theater;
            """)
            
            return cursor.fetchall()
            
        except:
            pass
        
        finally:
            cursor.close()
    

    @staticmethod
    def insert_city_info(conn: Connection, city_seq: str, city_name: str) -> Optional[any]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO city VALUES ('{city_seq}', '{city_name}')
            """)
            
            if cursor.rowcount > 0:
                return TheaterResult.SUCCESS
            
            else:
                return TheaterResult.FAIL
        
        except IntegrityError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.CONFLICT
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.INTERNAL_SERVER_ERROR
            
        finally:
            conn.commit()
            cursor.close()
            
    
    @staticmethod
    def insert_gu_info(conn: Connection, gu_seq: str, gu_name: str, city_seq: str) -> Optional[any]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO gu VALUES ('{gu_seq}', '{gu_name}', '{city_seq}')
            """)
            
            if cursor.rowcount > 0:
                return TheaterResult.SUCCESS
            
            else:
                return TheaterResult.FAIL
        
        except IntegrityError as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.CONFLICT
            
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.INTERNAL_SERVER_ERROR
            
        finally:
            conn.commit()
            cursor.close()
            
    
    @staticmethod
    def insert_theater_info(conn: Connection, theater_seq: str, place_name: str, address: str, road_address: str, lat: float, long: float, gu_seq: str) -> Optional[any]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO theater VALUES ('{theater_seq}', '{place_name}', '{address}', '{road_address}', {lat}, {long}, '{gu_seq}');
            """)
            
            if cursor.rowcount > 0:
                return TheaterResult.SUCCESS
            
            else:
                return TheaterResult.FAIL
        
        except IntegrityError as e:
            # print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.CONFLICT
            
        except Exception as e:
            # print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return TheaterResult.INTERNAL_SERVER_ERROR
            
        finally:
            conn.commit()
            cursor.close()
    