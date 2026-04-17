from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

app = Flask(__name__)

# DB connection
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/rider-login', methods=['GET', 'POST'])
def rider_login():
    error = None
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id == 'rider123' and password == 'riderpass':
            return render_template('booking.html')
        error = 'Invalid Rider ID or password.'
    return render_template('rider_login.html', error=error)

@app.route('/rider-signup', methods=['GET', 'POST'])
def rider_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        password = request.form.get('password')
        # Dummy signup - in real app, save to DB
        # For now, just redirect to login
        return redirect(url_for('rider_login'))
    return render_template('rider_signup.html')

@app.route('/driver-login', methods=['GET', 'POST'])
def driver_login():
    error = None
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id == 'driver123' and password == 'driverpass':
            return render_template('booking.html')
        error = 'Invalid Driver ID or password.'
    return render_template('driver_login.html', error=error)

@app.route('/driver-signup', methods=['GET', 'POST'])
def driver_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        password = request.form.get('password')
        car_make = request.form.get('car_make')
        car_model = request.form.get('car_model')
        reg_number = request.form.get('reg_number')
        aadhaar_number = request.form.get('aadhaar_number')
        # In a real app save driver data to DB here
        return redirect(url_for('driver_login'))
    return render_template('driver_signup.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id == 'admin123' and password == 'adminpass':
            return redirect(url_for('book'))
        error = 'Invalid Admin ID or password.'
    return render_template('admin_login.html', error=error)

@app.route('/book')
def book():
    return render_template('booking.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    phone = request.form['phone']
    pickup = request.form['pickup']
    drop = request.form['drop']
    distance = request.form['distance']
    fare = request.form['fare']
    ride_date = request.form['ride_date']
    ride_time = request.form['ride_time']

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO bookings (name, phone, pickup_location, drop_location, distance, fare, ride_date, ride_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (name, phone, pickup, drop, distance, fare, ride_date, ride_time)
    )
    db.commit()

    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
