from pymysql.connections import Connection


def check_exist_table(conn: Connection, table: str) -> bool:
    cursor = conn.cursor()
    result = cursor.execute(f"SHOW TABLES LIKE '{table}';")
    cursor.close()

    return result != 0


def create_account_table(conn: Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE `account`(
            `account_seq` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            `id` VARCHAR(15) NOT NULL UNIQUE,
            `password` VARCHAR(64) NOT NULL,
            `nickname` VARCHAR(20) NOT NULL UNIQUE,
            `email` VARCHAR(30) NOT NULL,
            `phone` VARCHAR(13) NOT NULL,
            `signup_date` DATETIME DEFAULT NOW(),
            `birthday` DATE DEFAULT NULL,
            `profile_image` TEXT DEFAULT NULL,
            `password_date` DATETIME NOT NULL,
            `like_categories` TEXT DEFAULT ('[]'),
            INDEX (`account_seq`)
        );
    """)
    conn.commit()
    cursor.close()


def create_category_table(conn: Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
       CREATE TABLE `category` (
           `category_seq` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
           `name` TEXT NOT NULL
       );
    """)
    cursor.close()


def setting(conn: Connection) -> None:
    # , "movie", "cinema", "pay", "ticket", "score"]
    table_list = ["account", "category"]

    for table in table_list:
        if not check_exist_table(conn, table):
            exec(f"create_{table}_table(conn)")
