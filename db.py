import mysql.connector
from mysql.connector import Error
import os

DB_CONFIG = {
    'host':     os.environ.get('MYSQLHOST',     os.environ.get('DB_HOST',     '127.0.0.1')),
    'port': int(os.environ.get('MYSQLPORT',     os.environ.get('DB_PORT',     '3306'))),
    'user':     os.environ.get('MYSQLUSER',     os.environ.get('DB_USER',     'root')),
    'password': os.environ.get('MYSQLPASSWORD', os.environ.get('DB_PASSWORD', 'sqlbook123')),
    'database': os.environ.get('MYSQLDATABASE', os.environ.get('DB_NAME',     'raidlink_db'))
}

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def init_db():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rider_Details (
                id             INT          AUTO_INCREMENT PRIMARY KEY,
                username       VARCHAR(100) NOT NULL,
                mobile         BIGINT       NOT NULL,
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
                registered_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        ALLOWED_COLS = {
            'licence_validity', 'fitness_validity', 'pollution_validity', 'permit_validity',
            'licence_img', 'rc_img', 'aadhaar_img', 'permit_img', 'pollution_img',
            'profile_photo', 'car_color'
        }
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
            ('car_color',          'VARCHAR(50) DEFAULT NULL'),
        ]:
            if col not in ALLOWED_COLS:
                continue
            try:
                cursor.execute(f"ALTER TABLE Driver_Details ADD COLUMN `{col}` {definition}")
                conn.commit()
            except Exception:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Trip_Details (
                id              INT           AUTO_INCREMENT PRIMARY KEY,
                rider_id        INT           DEFAULT NULL,
                pickup_location VARCHAR(255)  NOT NULL,
                drop_location   VARCHAR(255)  NOT NULL,
                distance_km     DECIMAL(8,2)  NOT NULL,
                fare            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                ride_date       DATE          NOT NULL,
                ride_time       TIME          NOT NULL,
                accepted_by     VARCHAR(100)  DEFAULT NULL,
                otp             CHAR(4)       DEFAULT NULL,
                status          ENUM('Confirmed','Completed','Cancelled') NOT NULL DEFAULT 'Confirmed',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        ALLOWED_TRIP_COLS = {'rider_id', 'accepted_by', 'otp'}
        for col, definition in [
            ('rider_id',    'INT DEFAULT NULL AFTER id'),
            ('accepted_by', 'VARCHAR(100) DEFAULT NULL AFTER ride_time'),
            ('otp',         'CHAR(4) DEFAULT NULL AFTER accepted_by'),
        ]:
            if col not in ALLOWED_TRIP_COLS:
                continue
            try:
                cursor.execute(f"ALTER TABLE Trip_Details ADD COLUMN `{col}` {definition}")
                conn.commit()
            except Exception:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Driver_Skipped_Trips (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                driver_name VARCHAR(100) NOT NULL,
                trip_id     INT NOT NULL,
                UNIQUE KEY uq_driver_trip (driver_name, trip_id)
            )
        """)

        # Driver online status tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Driver_Online_Status (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                driver_username VARCHAR(100) NOT NULL UNIQUE,
                is_online       BOOLEAN NOT NULL DEFAULT FALSE,
                last_seen       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                location_lat    DECIMAL(10,8) DEFAULT NULL,
                location_lng    DECIMAL(11,8) DEFAULT NULL,
                current_trip_id INT DEFAULT NULL,
                priority_score  INT NOT NULL DEFAULT 0,
                INDEX idx_online (is_online),
                INDEX idx_last_seen (last_seen),
                INDEX idx_location (location_lat, location_lng)
            )
        """)

        # Booking assignment queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Booking_Queue (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                trip_id         INT NOT NULL UNIQUE,
                assigned_driver VARCHAR(100) DEFAULT NULL,
                assignment_time DATETIME DEFAULT NULL,
                timeout_at      DATETIME DEFAULT NULL,
                retry_count     INT NOT NULL DEFAULT 0,
                status          ENUM('pending','assigned','accepted','expired') NOT NULL DEFAULT 'pending',
                created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_timeout (timeout_at),
                FOREIGN KEY (trip_id) REFERENCES Trip_Details(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Database initialised successfully.")
    except Error as e:
        print(f"[DB INIT ERROR] {e}")
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass
