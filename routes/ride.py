from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Ride, TripRequest
from uuid import uuid4
from App import socketio

# Define the Blueprint
ride_bp = Blueprint('ride', __name__, url_prefix='/ride')

@ride_bp.route('/<int:ride_request_id>/accept', methods=['POST'])
@login_required
def accept_ride(ride_request_id):
    """
    Handles a driver accepting a ride request.
    Creates a Ride session and notifies the rider.
    """
    # 1. Load the ride request
    request_obj = TripRequest.query.get_or_404(ride_request_id)
    
    # 2. Generate a short unique ride_id
    new_ride_id = "R" + uuid4().hex[:8].upper()
    
    # 3. Create the active Ride record
    ride = Ride(
        ride_id=new_ride_id,
        driver_id=current_user.id,
        rider_id=request_obj.rider_id,
        status="active"
    )
    
    # 4. Mark request as accepted
    request_obj.status = "Accepted"
    
    try:
        db.session.add(ride)
        db.session.commit()
        
        # 5. Notify the rider via Socket.IO
        # We emit to a room named after the rider's ID so their specific client receives it
        socketio.emit('ride_accepted', {
            'ride_id': new_ride_id,
            'driver_name': current_user.username
        }, room=str(request_obj.rider_id))
        
        return redirect(url_for('ride.driver_view', ride_id=new_ride_id))
        
    except Exception as e:
        db.session.rollback()
        flash("Error accepting ride. Please try again.")
        print(f"Error: {e}")
        return redirect(url_for('driver_home', username=current_user.username))

@ride_bp.route('/<ride_id>/driver')
@login_required
def driver_view(ride_id):
    """
    Serves the driver-facing navigation page.
    """
    return render_template("driver_navigate.html", ride_id=ride_id, driver_id=current_user.id)

@ride_bp.route('/<ride_id>/rider')
@login_required
def rider_view(ride_id):
    """
    Serves the rider-facing tracking page.
    """
    return render_template("rider_tracking.html", ride_id=ride_id)
