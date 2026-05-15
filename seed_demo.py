"""
seed_demo.py — Generate demo accounts and bookings for PAYANUM testing.
Run: python seed_demo.py
"""
import sys
from werkzeug.security import generate_password_hash
import random
from datetime import date, timedelta
from db import get_db

def h(pw): return generate_password_hash(pw)

LOCATIONS = [
    ("Anna Nagar", "T Nagar"),       ("Adyar", "Velachery"),
    ("Tambaram", "Guindy"),          ("Porur", "Koyambedu"),
    ("Chromepet", "Sholinganallur"), ("Perambur", "Egmore"),
    ("Mylapore", "Nungambakkam"),    ("Vadapalani", "Ashok Nagar"),
    ("Pallavaram", "Medavakkam"),    ("Ambattur", "Avadi"),
    ("Besant Nagar", "Thiruvanmiyur"),("Kodambakkam", "Saidapet"),
    ("Kolathur", "Villivakkam"),     ("Poonamallee", "Maduravoyal"),
    ("Nanganallur", "Alandur"),
]

CAR_DATA = [
    ("Toyota",  "Innova",  "White",  "TN01"),
    ("Maruti",  "Swift",   "Silver", "TN02"),
    ("Honda",   "City",    "Black",  "TN03"),
    ("Hyundai", "Creta",   "Blue",   "TN04"),
    ("Tata",    "Nexon",   "Red",    "TN05"),
    ("Kia",     "Seltos",  "Grey",   "TN06"),
    ("Ford",    "EcoSport", "White", "TN07"),
    ("Renault", "Kwid",    "Orange", "TN08"),
    ("Mahindra","Scorpio", "Black",  "TN09"),
    ("Suzuki",  "Ertiga",  "Silver", "TN10"),
]

FIRST = ["Arjun","Priya","Rahul","Sneha","Karthik","Divya","Vijay","Anitha",
         "Suresh","Meena","Ravi","Lakshmi","Arun","Kavitha","Siva","Nithya",
         "Ganesh","Pooja","Murugan","Saranya","Deepak","Revathi","Ajay","Bhavani",
         "Senthil","Geetha","Manoj","Usha","Praveen","Radha","Vinoth","Sumathi",
         "Balaji","Kamala","Dinesh","Valli","Harish","Selvi","Naveen","Padma"]

LAST  = ["Kumar","Raj","Sharma","Devi","Krishnan","Nair","Pillai","Reddy",
         "Iyer","Murugan","Rajan","Balan","Selvam","Natarajan","Sundaram"]

def rname(): return f"{random.choice(FIRST)}{random.choice(LAST)}"
def rdate(start_days=0, end_days=365):
    return date.today() + timedelta(days=random.randint(start_days, end_days))

def seed():
    conn = get_db()
    if not conn:
        print("[ERROR] Cannot connect to DB"); sys.exit(1)
    cur = conn.cursor()

    # ── 60 Riders ────────────────────────────────────────────
    print("Creating riders...")
    rider_ids = []
    for i in range(1, 61):
        uname = f"rider{i:03d}"
        email = f"rider{i:03d}@demo.com"
        mobile = 9000000000 + i
        try:
            cur.execute(
                "INSERT INTO Rider_Details (username, mobile, email, password_hash) VALUES (%s,%s,%s,%s)",
                (uname, mobile, email, h("Demo@1234"))
            )
            conn.commit()
            rider_ids.append(cur.lastrowid)
            print(f"  ✓ {uname}")
        except Exception:
            cur.execute("SELECT id FROM Rider_Details WHERE username=%s", (uname,))
            row = cur.fetchone()
            if row: rider_ids.append(row[0])
            print(f"  ~ {uname} already exists")

    # ── 50 Drivers ───────────────────────────────────────────
    print("\nCreating drivers...")
    driver_names = []
    for i in range(1, 51):
        uname  = f"driver{i:03d}"
        email  = f"driver{i:03d}@demo.com"
        mobile = 8000000000 + i
        car    = CAR_DATA[i % len(CAR_DATA)]
        reg    = f"{car[3]}AB{1000+i:04d}"
        aadhaar= f"{100000000000 + i:012d}"
        vdate  = str(rdate(180, 730))
        try:
            cur.execute(
                """INSERT INTO Driver_Details
                   (username, mobile, email, password_hash, car_make, car_model, car_color,
                    reg_number, aadhaar_number, licence_validity, fitness_validity,
                    pollution_validity, permit_validity, account_status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active')""",
                (uname, mobile, email, h("Demo@1234"),
                 car[0], car[1], car[2], reg, aadhaar,
                 vdate, vdate, vdate, vdate)
            )
            conn.commit()
            driver_names.append(uname)
            print(f"  ✓ {uname} — {car[0]} {car[1]} ({reg})")
        except Exception:
            driver_names.append(uname)
            print(f"  ~ {uname} already exists")

    # ── 200 Bookings ─────────────────────────────────────────
    print("\nCreating bookings...")
    statuses   = ['Confirmed', 'Completed', 'Cancelled']
    weights    = [0.3, 0.55, 0.15]
    booking_count = 0

    for rider_id in rider_ids:
        num_bookings = random.randint(2, 5)
        for _ in range(num_bookings):
            loc        = random.choice(LOCATIONS)
            pickup, drop = loc if random.random() > 0.5 else (loc[1], loc[0])
            distance   = round(random.uniform(3, 45), 1)
            fare       = round(distance * 25, 2)
            ride_date  = str(rdate(-60, 30))
            ride_time  = f"{random.randint(6,22):02d}:{random.choice(['00','15','30','45'])}"
            otp        = str(random.randint(1000, 9999))
            status     = random.choices(statuses, weights)[0]
            accepted_by= random.choice(driver_names) if status in ('Completed',) else (
                         random.choice(driver_names) if random.random() > 0.4 else None)
            if status == 'Cancelled': accepted_by = None

            cur.execute(
                """INSERT INTO Trip_Details
                   (rider_id, pickup_location, drop_location, distance_km, fare,
                    ride_date, ride_time, otp, accepted_by, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (rider_id, pickup, drop, distance, fare,
                 ride_date, ride_time, otp, accepted_by, status)
            )
            booking_count += 1

    conn.commit()
    cur.close(); conn.close()

    print(f"\n{'='*50}")
    print(f"  Riders  created : {len(rider_ids)}")
    print(f"  Drivers created : {len(driver_names)}")
    print(f"  Bookings created: {booking_count}")
    print(f"  Login password  : Demo@1234")
    print(f"  Sample rider    : rider001 / Demo@1234")
    print(f"  Sample driver   : driver001 / Demo@1234")
    print(f"{'='*50}")

if __name__ == '__main__':
    seed()
