from typing import Tuple, Dict, List, Optional
from enum import Enum
import traceback
import pymysql

class CategoryResult(Enum):
    FAIL = 0
    SUCCESS = 1
    CONFLICT = 2
    INTERNAL_SERVER_ERROR = 3
    
    
class Category:
    @staticmethod
    def load_category_list(conn: pymysql.connections.Connection) -> Tuple[CategoryResult, Optional[List[Dict[str, str]]]]:
        try:
            cursor = conn.cursor()    
            cursor.execute(f"""
                SELECT * FROM category;
            """)
            
            result = cursor.fetchall()
            return (CategoryResult.SUCCESS, result)
            
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CategoryResult.INTERNAL_SERVER_ERROR, None)
            
        finally:
            cursor.close()
            
    
    @staticmethod
    def load_category_seq(conn: pymysql.connections.Connection, category_name: str) -> Tuple[CategoryResult, Optional[int]]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT category_seq FROM category WHERE name='{category_name}';
            """)
            result = cursor.fetchall()
            
            return (CategoryResult.SUCCESS, result[0])
        
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CategoryResult.INTERNAL_SERVER_ERROR, None)
         
        finally:
            cursor.close()
            
            
    @staticmethod
    def check_exist_category(conn: pymysql.connections.Connection, category_name: str) -> bool:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT name FROM category WHERE name='{category_name}';
            """)
            result = cursor.fetchall()
            
            return result != ()
        
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return True
         
        finally:
            cursor.close()
            
            
    @staticmethod
    def insert_category(conn: pymysql.connections.Connection, category_name: str) -> CategoryResult:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO category(name) VALUES ('{category_name}');
            """)            
            conn.commit()
            
            result = cursor.fetchall()
            return CategoryResult.SUCCESS if result == () else CategoryResult.FAIL

        except pymysql.err.OperationalError as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return CategoryResult.CONFLICT
            
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return CategoryResult.INTERNAL_SERVER_ERROR

        finally:
            cursor.close()
            