from flask import Flask, render_template, request
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
    return render_template('index.html')

@app.route('/book')
def book():
    return render_template('booking.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    phone = request.form['phone']
    pickup = request.form['pickup']
    drop = request.form['drop']

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO bookings (name, phone, pickup_location, drop_location) VALUES (%s, %s, %s, %s)",
        (name, phone, pickup, drop)
    )
    db.commit()

    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
