from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))

class TripRequest(db.Model):
    __tablename__ = 'trip_details'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pickup_location = db.Column(db.String(255))
    drop_location = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Confirmed")

class Ride(db.Model):
    __tablename__ = 'rides'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "RIDE001"
    
    # Foreign keys - assuming a 'users' table exists
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(20), default="searching")  # searching, accepted, active, completed
    
    driver_lat = db.Column(db.Float, nullable=True)
    driver_lng = db.Column(db.Float, nullable=True)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_location(self, lat, lng):
        """
        Updates the driver's last known GPS location and saves to database.
        """
        self.driver_lat = lat
        self.driver_lng = lng
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_active(cls, ride_id):
        """
        Returns the ride object for a given ride_id if it exists.
        """
        return cls.query.filter_by(ride_id=ride_id).first()
