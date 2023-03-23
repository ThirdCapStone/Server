from typing import Dict
import traceback
import pymysql

def load_mysql_user_info() -> Dict[str, str]:
    try:
        f = open("user_info.txt", "r")
        
    except FileNotFoundError:
        raise FileNotFoundError("Don't remove user_info.txt file!")

    lines = list(map(lambda x: x.replace("\n", ""), f.readlines()))
    keys, values = list(), list()

    for line in lines:
        split_line = list(map(lambda x: x.strip(), line.split("=")))
        if "" in split_line:
            raise ValueError("Please Enter Information on user_info.txt")
        
        keys.append(split_line[0])
        values.append(split_line[1])

    if len(keys) != len(values):
        raise IndexError("Please Match Keys And Values")
    
    must_info = ["host", "user", "password"]
    for info in must_info:
        if info not in keys:
            raise KeyError("Insufficient information entered")
    
    return {keys[i] : values[i] for i in range(len(keys))}


def db_connection() -> pymysql.connections.Connection:
    user_info = load_mysql_user_info()
    
    try:
        return pymysql.connect(
            **user_info
        )

    except pymysql.err.OperationalError as e:
        print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
    
    except TypeError as e:
        print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")