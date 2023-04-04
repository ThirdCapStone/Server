from pymysql.connections import Connection
from db.connection import load_mysql_user_info, db_connection
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


def test_db_connection():
    conn = db_connection()

    assert isinstance(conn, Connection)


def test_load_mysql_user_info():
    info = load_mysql_user_info()

    assert len(info.keys()) > 3
