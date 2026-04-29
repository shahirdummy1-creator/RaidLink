import mysql.connector
import config

def check_db():
    try:
        conn = mysql.connector.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB
        )
        cur = conn.cursor()
        cur.execute("SELECT id, otp, status FROM Trip_Details ORDER BY id DESC LIMIT 5;")
        rows = cur.fetchall()
        print("ID | OTP | Status")
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_db()
