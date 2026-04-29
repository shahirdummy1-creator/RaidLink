#!/usr/bin/env python3

import os
from dotenv import load_dotenv
load_dotenv()

# Test Razorpay integration
try:
    import razorpay
    print("[OK] Razorpay package imported successfully")
    
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    
    print(f"[OK] Key ID: {RAZORPAY_KEY_ID}")
    print(f"[OK] Key Secret: {'Set' if RAZORPAY_KEY_SECRET else 'Not Set'}")
    
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        print("[OK] Razorpay client created successfully")
        
        # Test creating an order
        order_data = {
            'amount': 5000,  # Rs.50 in paise
            'currency': 'INR',
            'receipt': 'test_receipt_123',
            'payment_capture': 1
        }
        
        order = client.order.create(data=order_data)
        print("[OK] Test order created successfully:")
        print(f"  Order ID: {order['id']}")
        print(f"  Amount: Rs.{order['amount']/100}")
        print(f"  Status: {order['status']}")
        print("\n[SUCCESS] Razorpay is working correctly!")
        
    else:
        print("[ERROR] Razorpay credentials not found")
        
except ImportError as e:
    print(f"[ERROR] Razorpay import failed: {e}")
except Exception as e:
    print(f"[ERROR] Razorpay test failed: {e}")