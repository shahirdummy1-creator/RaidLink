import mysql.connector
from mysql.connector import Error
import os

DB_CONFIG = {
    'host':     os.environ.get('MYSQLHOST',     os.environ.get('DB_HOST',     '127.0.0.1')),
    'user':     os.environ.get('MYSQLUSER',     os.environ.get('DB_USER',     'root')),
    'password': os.environ.get('MYSQLPASSWORD', os.environ.get('DB_PASSWORD', 'sqlbook123')),
    'database': os.environ.get('MYSQLDATABASE', os.environ.get('DB_NAME',     'raidlink_db')),
    'port':     int(os.environ.get('MYSQLPORT', os.environ.get('DB_PORT',     3306)))
}

def get_db():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def init_db():
    """Create database and tables if they don't exist."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()

        db_name = DB_CONFIG['database']
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{db_name}`")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rider_Details (
                id             INT          AUTO_INCREMENT PRIMARY KEY,
                username       VARCHAR(100) NOT NULL,
                mobile         BIGINT  NOT NULL,
                email          VARCHAR(150) NOT NULL UNIQUE,
                password_hash  VARCHAR(255) NOT NULL,
                account_status ENUM('Active','Suspended') NOT NULL DEFAULT 'Active',
                registered_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Driver_Details (
                id                 INT          AUTO_INCREMENT PRIMARY KEY,
                username           VARCHAR(100) NOT NULL,
                mobile             BIGINT       NOT NULL,
                email              VARCHAR(150) NOT NULL UNIQUE,
                password_hash      VARCHAR(255) NOT NULL,
                car_make           VARCHAR(100) NOT NULL,
                car_model          VARCHAR(100) NOT NULL,
                reg_number         VARCHAR(50)  NOT NULL UNIQUE,
                aadhaar_number     CHAR(12)     NOT NULL,
                licence_validity   DATE         DEFAULT NULL,
                fitness_validity   DATE         DEFAULT NULL,
                pollution_validity DATE         DEFAULT NULL,
                permit_validity    DATE         DEFAULT NULL,
                account_status     ENUM('Active','Suspended') NOT NULL DEFAULT 'Active',
                registered_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add validity columns to existing tables if missing
        for col, definition in [
            ('licence_validity',   'DATE DEFAULT NULL'),
            ('fitness_validity',   'DATE DEFAULT NULL'),
            ('pollution_validity', 'DATE DEFAULT NULL'),
            ('permit_validity',    'DATE DEFAULT NULL'),
            ('licence_img',        'VARCHAR(255) DEFAULT NULL'),
            ('rc_img',             'VARCHAR(255) DEFAULT NULL'),
            ('aadhaar_img',        'VARCHAR(255) DEFAULT NULL'),
            ('permit_img',         'VARCHAR(255) DEFAULT NULL'),
            ('pollution_img',      'VARCHAR(255) DEFAULT NULL'),
            ('profile_photo',      'VARCHAR(255) DEFAULT NULL'),
        ]:
            try:
                cursor.execute(f"ALTER TABLE Driver_Details ADD COLUMN {col} {definition}")
                conn.commit()
            except Exception:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Trip_Details (
                id              INT           AUTO_INCREMENT PRIMARY KEY,
                pickup_location VARCHAR(255)  NOT NULL,
                drop_location   VARCHAR(255)  NOT NULL,
                distance_km     DECIMAL(8,2)  NOT NULL,
                fare            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                ride_date       DATE          NOT NULL,
                ride_time       TIME          NOT NULL,
                accepted_by     VARCHAR(100)  DEFAULT NULL,
                status          ENUM('Confirmed','Completed','Cancelled') NOT NULL DEFAULT 'Confirmed',
                created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add columns if they don't exist (for existing tables)
        try:
            cursor.execute("ALTER TABLE Trip_Details ADD COLUMN accepted_by VARCHAR(100) DEFAULT NULL AFTER ride_time")
            conn.commit()
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE Trip_Details ADD COLUMN rider_id INT DEFAULT NULL AFTER id")
            conn.commit()
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE Trip_Details ADD COLUMN otp CHAR(4) DEFAULT NULL AFTER accepted_by")
            conn.commit()
        except Exception:
            pass  # column already exists

        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] RaidLink_DB initialised successfully.")
    except Error as e:
        print(f"[DB INIT ERROR] {e}")
