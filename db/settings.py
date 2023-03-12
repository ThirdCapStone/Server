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
            `id` VARCHAR(15) NOT NULL,
            `password` VARCHAR(64) NOT NULL,
            `nickname` VARCHAR(20) NOT NULL,
            `email` VARCHAR(50) NOT NULL,
            `phone` VARCHAR(13) NOT NULL,
            `signup_date` DATETIME DEFAULT NOW(),
            `birthday` DATE NOT NULL,
            `profile_image` TEXT DEFAULT NULL,
            `password_date` DATETIME NOT NULL,
            INDEX (`account_seq`)
        );
    """)
    conn.commit()
    cursor.close()


def create_movie_table(conn: Connection) -> bool:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE `movie`(
            `movie_seq` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY
        );
    """)
    cursor.close()


def create_category_table(conn: Connection) -> bool:
    cursor = conn.cursor()
    cursor.execute("""
       CREATE TABLE `category` (
           `category_seq` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
           `account_seq` BIGINT UNSIGNED DEFAULT NULL,
           `movie_seq` BIGINT UNSIGNED DEFAULT NULL,
           `name` TEXT NOT NULL,
           FOREIGN KEY (`account_seq`) REFERENCES `account` (`account_seq`),
           FOREIGN KEY (`movie_seq`) REFERENCES `movie` (`movie_seq`)
       );
    """)
    cursor.close()


def key_setting(conn: Connection) -> bool:
    pass


def setting(conn: Connection) -> None:
    table_list = ["account", "movie", "category"]#, "cinema", "pay", "ticket", "score"]

    for table in table_list:
        if not check_exist_table(conn, table):
            exec(f"create_{table}_table(conn)")