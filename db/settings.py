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
    

def create_movie_table(conn: Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE `movie` (
            `movie_seq` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            `korean_title` TEXT NOT NULL,
            `english_title` TEXT DEFAULT (''),
            `summary` TEXT DEFAULT (''),
            `main_photo_image` TEXT NULL DEFAULT NULL,
            `release_date` DATETIME NOT NULL,
            `running_time` INT	NULL DEFAULT NULL,
            `cookie_count` INT	NULL DEFAULT 0,
            `production_year` INT NOT NULL,
            `require_adult`	BOOLEAN NULL,
            `admission_code` TEXT NOT NULL,
            `casts`	TEXT NULL DEFAULT ('[]'),
            `studio` TEXT NULL DEAFULT NULL,
            `genres` TEXT NULL DEFAULT ('[]'),
            `total_audience_count` INT NULL	DEFAULT 0,
            `daum_average_rating` FLOAT NULL DEFAULT 0.0,
            INDEX (`movie_seq`)
        );
    """)
    cursor.close()


def setting(conn: Connection) -> None:
    table_list = ["account", "category", "movie"]#, "theater", "pay", "ticket"]

    for table in table_list:
        if not check_exist_table(conn, table):
            exec(f"create_{table}_table(conn)")
