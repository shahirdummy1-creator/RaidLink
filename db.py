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
            'profile_photo', 'car_color', 'admin_name', 'payment_id', 'payment_date', 'payment_expiry_date'
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
            ('admin_name',         'VARCHAR(100) DEFAULT NULL'),
            ('payment_id',         'VARCHAR(100) DEFAULT NULL'),
            ('payment_date',       'DATETIME DEFAULT NULL'),
            ('payment_expiry_date', 'DATE DEFAULT NULL'),
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Password_Reset_Tokens (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                user_id    INT NOT NULL,
                user_type  ENUM('rider','driver','admin') NOT NULL,
                email      VARCHAR(150) NOT NULL,
                token      VARCHAR(64) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user_type (user_id, user_type)
            )
        """)

        # Create Driver_Payments table (optional - for Razorpay integration)
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Driver_Payments (
                    id                  INT AUTO_INCREMENT PRIMARY KEY,
                    username            VARCHAR(100) NOT NULL,
                    razorpay_order_id   VARCHAR(100) NOT NULL,
                    razorpay_payment_id VARCHAR(100) NOT NULL,
                    amount              INT NOT NULL,
                    status              ENUM('pending','completed','failed') NOT NULL DEFAULT 'pending',
                    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_payment (razorpay_payment_id)
                )
            """)
        except Exception as e:
            print(f"[DB] Warning: Could not create Driver_Payments table: {e}")

        # Create Unmatched_Payments table for webhook processing
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Unmatched_Payments (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    payment_id VARCHAR(100) NOT NULL,
                    amount     DECIMAL(10,2) NOT NULL,
                    contact    VARCHAR(20) DEFAULT NULL,
                    email      VARCHAR(150) DEFAULT NULL,
                    processed  BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_payment_id (payment_id)
                )
            """)
        except Exception as e:
            print(f"[DB] Warning: Could not create Unmatched_Payments table: {e}")
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
