from flask import request
from flask_socketio import join_room, emit
from App import socketio
from models import db, Ride

@socketio.on('join_ride')
def handle_join_ride(data):
    ride_id = data.get('ride_id')
    role = data.get('role')
    
    if not ride_id:
        return

    # Join the private room for this specific ride
    join_room(ride_id)
    print(f"[SOCKET] {role} joined room: {ride_id}")

    # If rider joins, send them the last known location if available
    if role == 'rider':
        try:
            ride = Ride.get_active(ride_id)
            if ride and ride.driver_lat and ride.driver_lng:
                emit('driver_location', {
                    'lat': ride.driver_lat,
                    'lng': ride.driver_lng
                }, to=request.sid)
        except Exception as e:
            print(f"[SOCKET ERROR] Error fetching ride location: {e}")

@socketio.on('update_location')
def handle_update_location(data):
    ride_id = data.get('ride_id')
    lat = data.get('lat')
    lng = data.get('lng')

    if not ride_id or lat is None or lng is None:
        return

    try:
        # Validate coordinates are valid floats
        lat = float(lat)
        lng = float(lng)

        # Update the database
        ride = Ride.get_active(ride_id)
        if ride:
            ride.update_location(lat, lng)

            # Broadcast to everyone in the room except the driver (sender)
            emit('driver_location', {
                'lat': lat,
                'lng': lng,
                'speed': data.get('speed')
            }, to=ride_id, include_self=False)
            
    except ValueError:
        print(f"[SOCKET ERROR] Invalid lat/lng format: {lat}, {lng}")
    except Exception as e:
        print(f"[SOCKET ERROR] Error updating location: {e}")

@socketio.on('ride_completed')
def handle_ride_completed(data):
    ride_id = data.get('ride_id')
    
    if not ride_id:
        return

    try:
        ride = Ride.get_active(ride_id)
        if ride:
            ride.status = "completed"
            db.session.commit()
            
            # Notify everyone in the room that the ride has ended
            emit('ride_ended', {'ride_id': ride_id}, to=ride_id)
            print(f"[SOCKET] Ride {ride_id} marked as completed")
    except Exception as e:
        print(f"[SOCKET ERROR] Error completing ride: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[SOCKET] Client disconnected: {request.sid}")
