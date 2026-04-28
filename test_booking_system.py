#!/usr/bin/env python3
"""
Test script to verify booking distribution system
"""
import requests
import json
import time

BASE_URL = "http://localhost:7860"

def test_booking_system():
    print("🔍 Testing Booking Distribution System")
    print("=" * 50)
    
    # 1. Set driver1 online
    print("1. Setting driver1 online...")
    response = requests.get(f"{BASE_URL}/api/set-driver-online/driver1")
    if response.status_code == 200:
        print("✅ Driver1 set online")
    else:
        print("❌ Failed to set driver1 online")
        return
    
    # 2. Check debug info
    print("\n2. Checking system status...")
    response = requests.get(f"{BASE_URL}/api/debug-booking-system")
    if response.status_code == 200:
        debug_info = response.json()
        print(f"📊 Online drivers: {len(debug_info.get('all_drivers', []))}")
        print(f"📊 Available drivers: {len(debug_info.get('available_drivers', []))}")
        print(f"📊 Recent bookings: {len(debug_info.get('recent_bookings', []))}")
        print(f"📊 Booking queue: {len(debug_info.get('booking_queue', []))}")
        
        # Show available drivers
        for driver in debug_info.get('available_drivers', []):
            print(f"   🚗 {driver['username']} - {driver['total_assignments']} assignments")
    else:
        print("❌ Failed to get debug info")
        return
    
    # 3. Force distribution
    print("\n3. Forcing booking distribution...")
    response = requests.get(f"{BASE_URL}/api/force-distribute")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result.get('message', 'Distribution triggered')}")
    else:
        print("❌ Failed to force distribution")
    
    # 4. Check latest booking for driver1
    print("\n4. Checking latest booking for driver1...")
    response = requests.get(f"{BASE_URL}/api/latest-booking?driver=driver1")
    if response.status_code == 200:
        booking_data = response.json()
        if booking_data.get('booking'):
            booking = booking_data['booking']
            print(f"✅ Found booking #{booking['id']}")
            print(f"   📍 From: {booking['pickup_location']}")
            print(f"   📍 To: {booking['drop_location']}")
            print(f"   💰 Fare: {booking['fare']}")
            print(f"   ⏰ Remaining: {booking.get('remaining_seconds', 0)}s")
        else:
            print("❌ No booking found for driver1")
    else:
        print("❌ Failed to check booking for driver1")

if __name__ == "__main__":
    try:
        test_booking_system()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on port 7860")
    except Exception as e:
        print(f"❌ Error: {e}")