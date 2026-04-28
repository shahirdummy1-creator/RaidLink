#!/usr/bin/env python3
"""
Test script to verify booking distribution system
"""
import requests
import json
import time

BASE_URL = "http://localhost:7860"

def test_booking_system():
    print("🔍 Testing SIMPLIFIED Booking System")
    print("=" * 50)
    
    # 1. Set driver1 online
    print("1. Setting driver1 online...")
    response = requests.get(f"{BASE_URL}/api/set-driver-online/driver1")
    if response.status_code == 200:
        print("✅ Driver1 set online")
    else:
        print("❌ Failed to set driver1 online")
        return
    
    # 2. Create test booking
    print("\n2. Creating test booking...")
    response = requests.get(f"{BASE_URL}/api/create-test-booking")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result.get('message', 'Test booking created')}")
        trip_id = result.get('trip_id')
    else:
        print("❌ Failed to create test booking")
        return
    
    # 3. Check if driver1 can see the booking
    print("\n3. Checking if driver1 can see the booking...")
    time.sleep(2)  # Wait a moment
    response = requests.get(f"{BASE_URL}/api/latest-booking?driver=driver1")
    if response.status_code == 200:
        booking_data = response.json()
        if booking_data.get('booking'):
            booking = booking_data['booking']
            print(f"✅ Driver1 can see booking #{booking['id']}")
            print(f"   📍 From: {booking['pickup_location']}")
            print(f"   📍 To: {booking['drop_location']}")
            print(f"   💰 Fare: {booking['fare']}")
            print(f"   👤 Rider: {booking.get('rider_name', 'N/A')}")
        else:
            print("❌ Driver1 cannot see any booking")
    else:
        print("❌ Failed to check booking for driver1")
    
    # 4. Check debug info
    print("\n4. System debug info...")
    response = requests.get(f"{BASE_URL}/api/debug-booking-system")
    if response.status_code == 200:
        debug_info = response.json()
        print(f"📊 Total drivers: {len(debug_info.get('all_drivers', []))}")
        print(f"📊 Available drivers: {len(debug_info.get('available_drivers', []))}")
        print(f"📊 Recent bookings: {len(debug_info.get('recent_bookings', []))}")
        
        # Show recent bookings
        for booking in debug_info.get('recent_bookings', [])[:3]:
            status = booking.get('accepted_by') or 'Unassigned'
            print(f"   🚗 Trip #{booking['trip_id']}: {booking['pickup']} → {booking['drop']} ({status})")
    else:
        print("❌ Failed to get debug info")

if __name__ == "__main__":
    try:
        test_booking_system()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on port 7860")
        print("   Run: python App.py")
    except Exception as e:
        print(f"❌ Error: {e}")