from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_db, init_db
from werkzeug.utils import secure_filename
import hashlib
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta, datetime
import hmac

# Optional imports with error handling
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    print("Warning: Razorpay not available. Payment features will be disabled.")
    RAZORPAY_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available. Using system environment variables only.")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'raidlink_secret_2024')
app.permanent_session_lifetime = timedelta(days=7)

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Initialize Razorpay client only if credentials are available
razorpay_client = None
if RAZORPAY_AVAILABLE and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        print("Razorpay client initialized successfully")
    except Exception as e:
        print(f"Razorpay initialization failed: {e}")
else:
    print("Warning: Razorpay credentials not found or Razorpay not available. Payment features will be disabled.")

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'drivers')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def save_file(file, prefix):
    if file and file.filename and allowed_file(file.filename):
        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{prefix}.{ext}")
        path     = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return f"uploads/drivers/{filename}"
    return None

# ── Initialise DB on startup ──────────────────────────────────
init_db()


# ── Helpers ──────────────────────────────────────────────────
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def send_reset_email(email, reset_token, user_type):
    """Send password reset email"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER', 'raidlink.tech@gmail.com')
        smtp_pass = os.environ.get('SMTP_PASS', 'your_app_password')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = 'RaidLink - Password Reset Request'
        
        reset_url = f"{request.url_root}reset-password?token={reset_token}&type={user_type}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #0d6efd; margin: 0;">🚕 RaidLink Technologies</h1>
                    <p style="color: #666; margin: 5px 0;">Password Reset Request</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #0d6efd; margin-top: 0;">Reset Your Password</h2>
                    <p>We received a request to reset your password for your RaidLink {user_type.title()} account.</p>
                    <p>Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background: #0d6efd; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;
                                  display: inline-block;">Reset Password</a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{reset_url}" style="color: #0d6efd;">{reset_url}</a>
                    </p>
                </div>
                
                <div style="border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666;">
                    <p><strong>Security Notice:</strong></p>
                    <ul>
                        <li>This link will expire in 1 hour for security reasons</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Never share this link with anyone</li>
                    </ul>
                    <p style="margin-top: 20px;">© 2024 RaidLink Technologies. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def generate_reset_token():
    """Generate a secure reset token"""
    return hashlib.sha256(f"{random.randint(100000, 999999)}{datetime.now().isoformat()}".encode()).hexdigest()[:32]

def format_fare(val):
    """Format fare with ₹ symbol and apply minimum ₹200."""
    try:
        return f"\u20b9{max(float(val or 0), 200.0):.2f}"
    except (ValueError, TypeError):
        return "\u20b9200.00"

def parse_fare(fare_str):
    try:
        val = float(str(fare_str).replace('₹', '').replace(',', '').strip())
        return max(val, 200.0)  # minimum fare ₹200
    except (ValueError, AttributeError):
        return 200.0

def row_to_dict(cursor, row):
    return dict(zip([c[0] for c in cursor.description], row))

def fetchall_dict(cursor):
    return [dict(zip([c[0] for c in cursor.description], r)) for r in cursor.fetchall()]

def get_rider_id(username):
    """Return rider_id for username from session store or DB."""
    riders = session.setdefault('riders', {})
    if username in riders:
        return riders[username]
    # Restore from DB (server restart)
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Rider_Details WHERE username=%s AND account_status='Active'", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            riders[username] = row[0]
            session.modified = True
            return row[0]
    return None

def get_driver(username):
    """Always verify from DB — never serve suspended driver from cache."""
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, car_make, car_model, reg_number, profile_photo FROM Driver_Details WHERE username=%s AND account_status='Active'",
            (username,)
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            d = {'id': row[0], 'username': row[1], 'car': f"{row[2]} {row[3]}", 'reg': row[4], 'photo': row[5] or ''}
            session.setdefault('drivers', {})[username] = d
            session.modified = True
            return d
    session.get('drivers', {}).pop(username, None)
    session.modified = True
    return None


# ════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/welcome')
@app.route('/index')
def welcome():
    return render_template('welcome.html')

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'message': 'RaidLink API is running',
        'razorpay_available': razorpay_client is not None
    }), 200

@app.route('/home')
def home():
    return render_template('welcome.html')


# ── Rider ────────────────────────────────────────────────────

@app.route('/rider-login', methods=['GET', 'POST'])
def rider_login():
    error   = None
    success = request.args.get('registered')
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username FROM Rider_Details WHERE username=%s AND password_hash=%s AND account_status='Active'",
                (username, hash_password(password))
            )
            rider = cur.fetchone()
            cur.close(); conn.close()
            if rider:
                session.permanent = True
                riders = session.setdefault('riders', {})
                riders[rider[1]] = rider[0]
                session.modified = True
                return redirect(url_for('rider_bookings', username=rider[1]))
            error = 'Invalid username or password, or account suspended.'
        else:
            error = 'Database connection failed.'
    return render_template('rider_login.html', error=error, success=success)

@app.route('/rider-signup', methods=['GET', 'POST'])
def rider_signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
        mobile   = request.form.get('mobile').strip()
        email    = request.form.get('email').strip()
        password = request.form.get('password')
        conn = get_db()
        if conn:
            cur = conn.cursor()
            # check username already taken
            cur.execute("SELECT id FROM Rider_Details WHERE username=%s", (username,))
            if cur.fetchone():
                error = 'ID already taken. Please choose another username.'
                cur.close(); conn.close()
            else:
                try:
                    cur.execute(
                        "INSERT INTO Rider_Details (username, mobile, email, password_hash) VALUES (%s,%s,%s,%s)",
                        (username, mobile, email, hash_password(password))
                    )
                    conn.commit()
                    cur.close(); conn.close()
                    return redirect(url_for('rider_login', registered=1))
                except Exception:
                    error = 'Email already registered. Please login.'
                    cur.close(); conn.close()
        else:
            error = 'Database connection failed.'
    return render_template('rider_signup.html', error=error)

# ── Forget Password Routes ───────────────────────────────────

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    user_type = request.args.get('type', 'rider')  # rider, driver, or admin
    
    if request.method == 'POST':
        email = request.form.get('email').strip()
        user_type = request.form.get('user_type', 'rider')
        
        if not email:
            error = 'Please enter your email address.'
        else:
            conn = get_db()
            if conn:
                cur = conn.cursor()
                
                # Check if email exists based on user type
                if user_type == 'rider':
                    cur.execute("SELECT id, username FROM Rider_Details WHERE email=%s AND account_status='Active'", (email,))
                elif user_type == 'driver':
                    cur.execute("SELECT id, username FROM Driver_Details WHERE email=%s AND account_status='Active'", (email,))
                elif user_type == 'admin':
                    # For admin, check against environment variable
                    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@raidlink.com')
                    if email == admin_email:
                        # Create a temporary admin record for reset
                        user_data = (1, 'admin')
                    else:
                        user_data = None
                else:
                    user_data = None
                
                if user_type != 'admin':
                    user_data = cur.fetchone()
                
                if user_data:
                    # Generate reset token
                    reset_token = generate_reset_token()
                    expires_at = datetime.now() + timedelta(hours=1)
                    
                    # Store reset token in database
                    cur.execute(
                        "INSERT INTO Password_Reset_Tokens (user_id, user_type, email, token, expires_at) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE token=%s, expires_at=%s",
                        (user_data[0], user_type, email, reset_token, expires_at, reset_token, expires_at)
                    )
                    conn.commit()
                    
                    # Send reset email
                    if send_reset_email(email, reset_token, user_type):
                        success = f'Password reset link has been sent to {email}. Please check your inbox.'
                    else:
                        error = 'Failed to send reset email. Please try again later.'
                else:
                    error = f'No {user_type} account found with this email address.'
                
                cur.close(); conn.close()
            else:
                error = 'Database connection failed.'
    
    return render_template('forgot_password.html', error=error, success=success, user_type=user_type)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    user_type = request.args.get('type', 'rider')
    error = None
    success = None
    
    if not token:
        error = 'Invalid reset link.'
        return render_template('reset_password.html', error=error)
    
    conn = get_db()
    if not conn:
        error = 'Database connection failed.'
        return render_template('reset_password.html', error=error)
    
    cur = conn.cursor()
    
    # Verify token and check expiration
    cur.execute(
        "SELECT user_id, user_type, email FROM Password_Reset_Tokens WHERE token=%s AND user_type=%s AND expires_at > NOW()",
        (token, user_type)
    )
    token_data = cur.fetchone()
    
    if not token_data:
        error = 'Invalid or expired reset link. Please request a new password reset.'
        cur.close(); conn.close()
        return render_template('reset_password.html', error=error)
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 6:
            error = 'Password must be at least 6 characters long.'
        elif new_password != confirm_password:
            error = 'Passwords do not match.'
        else:
            # Update password based on user type
            hashed_password = hash_password(new_password)
            
            if user_type == 'rider':
                cur.execute("UPDATE Rider_Details SET password_hash=%s WHERE id=%s", (hashed_password, token_data[0]))
            elif user_type == 'driver':
                cur.execute("UPDATE Driver_Details SET password_hash=%s WHERE id=%s", (hashed_password, token_data[0]))
            elif user_type == 'admin':
                # For admin, update environment variable (in production, this should update a secure config)
                # For now, we'll show success but admin needs to update manually
                pass
            
            # Delete used token
            cur.execute("DELETE FROM Password_Reset_Tokens WHERE token=%s", (token,))
            conn.commit()
            
            success = 'Password has been reset successfully. You can now login with your new password.'
    
    cur.close(); conn.close()
    return render_template('reset_password.html', error=error, success=success, user_type=user_type)


# ── Driver ───────────────────────────────────────────────────

@app.route('/driver-login', methods=['GET', 'POST'])
def driver_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('user_id').strip()
        password = request.form.get('password')
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, car_make, car_model, reg_number, profile_photo FROM Driver_Details WHERE username=%s AND password_hash=%s AND account_status='Active'",
                (username, hash_password(password))
            )
            driver = cur.fetchone()
            cur.close(); conn.close()
            if driver:
                session.permanent = True
                drivers = session.setdefault('drivers', {})
                drivers[driver[1]] = {
                    'id':    driver[0],
                    'username': driver[1],
                    'car':   f"{driver[2]} {driver[3]}",
                    'reg':   driver[4],
                    'photo': driver[5] or ''
                }
                session.modified = True
                return redirect(url_for('driver_home', username=driver[1]))
        error = 'Invalid username or password, or account suspended.'
    return render_template('driver_login.html', error=error)

@app.route('/driver-signup', methods=['GET', 'POST'])
def driver_signup():
    return redirect(url_for('driver_signup_step1'))

@app.route('/driver-signup/step1', methods=['GET', 'POST'])
def driver_signup_step1():
    error = None
    form  = session.get('signup_step1', {})
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        mobile   = request.form.get('mobile', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        admin_name = request.form.get('admin_name', '').strip()
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM Driver_Details WHERE username=%s", (username,))
            if cur.fetchone():
                error = 'Username already taken. Please choose another.'
                cur.close(); conn.close()
            else:
                cur.close(); conn.close()
                profile_photo = save_file(request.files.get('profile_photo'), f"{secure_filename(username)}_profile")
                session['signup_step1'] = {
                    'username': username, 'mobile': mobile,
                    'email': email, 'password': hash_password(password),
                    'profile_photo': profile_photo, 'admin_name': admin_name
                }
                session.modified = True
                return redirect(url_for('driver_signup_step2'))
        else:
            error = 'Database connection failed.'
    return render_template('driver_signup_step1.html', error=error, form=form)

@app.route('/driver-signup/step2', methods=['GET', 'POST'])
def driver_signup_step2():
    if 'signup_step1' not in session:
        return redirect(url_for('driver_signup_step1'))
    error = None
    form  = session.get('signup_step2', {})
    if request.method == 'POST':
        session['signup_step2'] = {
            'car_make':      request.form.get('car_make', '').strip(),
            'car_model':     request.form.get('car_model', '').strip(),
            'car_color':     request.form.get('car_color', '').strip() or None,
            'reg_number':    request.form.get('reg_number', '').strip(),
            'aadhaar_number':request.form.get('aadhaar_number', '').strip()
        }
        session.modified = True
        return redirect(url_for('driver_signup_step3'))
    return render_template('driver_signup_step2.html', error=error, form=form)

@app.route('/driver-signup/step3', methods=['GET', 'POST'])
def driver_signup_step3():
    if 'signup_step1' not in session or 'signup_step2' not in session:
        return redirect(url_for('driver_signup_step1'))
    error = None
    if request.method == 'POST':
        s1 = session['signup_step1']
        s2 = session['signup_step2']
        prefix = secure_filename(s1['username'])
        licence_validity   = request.form.get('licence_validity') or None
        fitness_validity   = request.form.get('fitness_validity') or None
        pollution_validity = request.form.get('pollution_validity') or None
        permit_validity    = request.form.get('permit_validity') or None
        profile_photo = s1.get('profile_photo') or save_file(request.files.get('profile_photo'), f"{prefix}_profile")
        licence_img   = save_file(request.files.get('licence_img'),   f"{prefix}_licence")
        rc_img        = save_file(request.files.get('rc_img'),         f"{prefix}_rc")
        aadhaar_img   = save_file(request.files.get('aadhaar_img'),    f"{prefix}_aadhaar")
        permit_img    = save_file(request.files.get('permit_img'),     f"{prefix}_permit")
        pollution_img = save_file(request.files.get('pollution_img'),  f"{prefix}_pollution")
        
        # Store step 3 data in session for payment completion
        session['signup_step3'] = {
            'licence_validity': licence_validity,
            'fitness_validity': fitness_validity,
            'pollution_validity': pollution_validity,
            'permit_validity': permit_validity,
            'licence_img': licence_img,
            'rc_img': rc_img,
            'aadhaar_img': aadhaar_img,
            'permit_img': permit_img,
            'pollution_img': pollution_img,
            'profile_photo': profile_photo
        }
        session.modified = True
        
        # Redirect to payment page instead of completing signup
        return redirect(url_for('driver_payment'))
    return render_template('driver_signup_step3.html', error=error)

# ── Razorpay Payment Routes ──────────────────────────────────────────────────

@app.route('/driver-payment')
def driver_payment():
    if 'signup_step1' not in session or 'signup_step2' not in session or 'signup_step3' not in session:
        return redirect(url_for('driver_signup_step1'))
    
    # Check if Razorpay is available
    if not razorpay_client or not RAZORPAY_KEY_ID:
        # Fallback: Complete signup without payment for now
        return redirect(url_for('complete_signup_without_payment'))
    
    s1 = session['signup_step1']
    return render_template('driver_payment.html', 
                         driver_name=s1['username'],
                         razorpay_key_id=RAZORPAY_KEY_ID)

@app.route('/api/create-order', methods=['POST'])
def create_order():
    if not razorpay_client:
        return jsonify({'error': 'Payment service unavailable'}), 503
        
    try:
        # Amount in paise (₹50 = 5000 paise)
        amount = 5000
        currency = 'INR'
        receipt = f"driver_signup_{session.get('signup_step1', {}).get('username', 'unknown')}_{random.randint(1000, 9999)}"
        
        # Create Razorpay order
        order_data = {
            'amount': amount,
            'currency': currency,
            'receipt': receipt,
            'payment_capture': 1
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': RAZORPAY_KEY_ID
        })
    
    except Exception as e:
        print(f"Error creating Razorpay order: {e}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    if not razorpay_client or not RAZORPAY_KEY_SECRET:
        return jsonify({'error': 'Payment service unavailable'}), 503
        
    try:
        # Get payment details from request
        razorpay_order_id = request.json.get('razorpay_order_id')
        razorpay_payment_id = request.json.get('razorpay_payment_id')
        razorpay_signature = request.json.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({'error': 'Missing payment details'}), 400
        
        # Verify signature
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Payment verified successfully - Complete driver signup
        return complete_driver_signup_with_payment(razorpay_order_id, razorpay_payment_id)
            
    except Exception as e:
        print(f"Payment verification error: {e}")
        return jsonify({'error': 'Payment verification failed'}), 500

# Helper function to complete signup with payment
def complete_driver_signup_with_payment(razorpay_order_id, razorpay_payment_id):
    if 'signup_step1' in session and 'signup_step2' in session and 'signup_step3' in session:
        s1 = session['signup_step1']
        s2 = session['signup_step2']
        s3 = session['signup_step3']
        
        conn = get_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """INSERT INTO Driver_Details
                       (username, mobile, email, password_hash, car_make, car_model, car_color,
                        reg_number, aadhaar_number, licence_validity, fitness_validity,
                        pollution_validity, permit_validity,
                        licence_img, rc_img, aadhaar_img, permit_img, pollution_img, profile_photo, admin_name)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (s1['username'], s1['mobile'], s1['email'], s1['password'],
                     s2['car_make'], s2['car_model'], s2['car_color'],
                     s2['reg_number'], s2['aadhaar_number'],
                     s3['licence_validity'], s3['fitness_validity'], s3['pollution_validity'], s3['permit_validity'],
                     s3['licence_img'], s3['rc_img'], s3['aadhaar_img'], s3['permit_img'], s3['pollution_img'], s3['profile_photo'],
                     s1.get('admin_name'))
                )
                conn.commit()
                
                # Store payment details (optional - for record keeping)
                try:
                    cur.execute(
                        """INSERT INTO Driver_Payments (username, razorpay_order_id, razorpay_payment_id, amount, status)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (s1['username'], razorpay_order_id, razorpay_payment_id, 5000, 'completed')
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Payment record error: {e}")
                    # Continue even if payment record fails
                
                cur.close(); conn.close()
                
                # Clear signup session data
                session.pop('signup_step1', None)
                session.pop('signup_step2', None)
                session.pop('signup_step3', None)
                session.modified = True
                
                return jsonify({'success': True, 'message': 'Payment verified and account created successfully'})
                
            except Exception as e:
                print(f"Database error: {e}")
                cur.close(); conn.close()
                return jsonify({'error': 'Failed to create account'}), 500
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    else:
        return jsonify({'error': 'Signup session expired'}), 400

# Fallback route for completing signup without payment (temporary)
@app.route('/complete-signup-without-payment')
def complete_signup_without_payment():
    if 'signup_step1' in session and 'signup_step2' in session and 'signup_step3' in session:
        s1 = session['signup_step1']
        s2 = session['signup_step2']
        s3 = session['signup_step3']
        
        conn = get_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """INSERT INTO Driver_Details
                       (username, mobile, email, password_hash, car_make, car_model, car_color,
                        reg_number, aadhaar_number, licence_validity, fitness_validity,
                        pollution_validity, permit_validity,
                        licence_img, rc_img, aadhaar_img, permit_img, pollution_img, profile_photo, admin_name)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (s1['username'], s1['mobile'], s1['email'], s1['password'],
                     s2['car_make'], s2['car_model'], s2['car_color'],
                     s2['reg_number'], s2['aadhaar_number'],
                     s3['licence_validity'], s3['fitness_validity'], s3['pollution_validity'], s3['permit_validity'],
                     s3['licence_img'], s3['rc_img'], s3['aadhaar_img'], s3['permit_img'], s3['pollution_img'], s3['profile_photo'],
                     s1.get('admin_name'))
                )
                conn.commit()
                cur.close(); conn.close()
                
                # Clear signup session data
                session.pop('signup_step1', None)
                session.pop('signup_step2', None)
                session.pop('signup_step3', None)
                session.modified = True
                
                return redirect(url_for('driver_login'))
                
            except Exception as e:
                print(f"Database error: {e}")
                cur.close(); conn.close()
                return redirect(url_for('driver_signup_step1'))
        else:
            return redirect(url_for('driver_signup_step1'))
    else:
        return redirect(url_for('driver_signup_step1'))


# ── Driver App ───────────────────────────────────────────────

@app.route('/api/driver-status/<username>')
def api_driver_status(username):
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT account_status FROM Driver_Details WHERE username=%s", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            return jsonify({'status': row[0]})
    return jsonify({'status': 'Unknown'})

@app.route('/api/driver-data/<username>')
def api_driver_data(username):
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT email, mobile FROM Driver_Details WHERE username=%s", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            return jsonify({'email': row[0], 'mobile': row[1]})
    return jsonify({'email': '', 'mobile': ''})

@app.route('/api/latest-booking')
def api_latest_booking():
    from flask import jsonify
    driver_name = request.args.get('driver', '')
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT t.id, t.rider_id, t.pickup_location, t.drop_location,
                      t.distance_km, t.fare, t.ride_date, t.ride_time,
                      t.accepted_by, t.otp, t.status,
                      r.username AS rider_name, r.mobile AS rider_mobile
               FROM Trip_Details t
               LEFT JOIN Rider_Details r ON r.id = t.rider_id
               WHERE t.status='Confirmed' AND (t.accepted_by IS NULL OR t.accepted_by='')
               AND t.rider_id IS NOT NULL
               AND t.id NOT IN (
                   SELECT trip_id FROM Driver_Skipped_Trips WHERE driver_name=%s
               )
               ORDER BY t.id DESC LIMIT 1""",
            (driver_name,)
        )
        row = cur.fetchone()
        if row:
            b = row_to_dict(cur, row)
            b['fare']      = format_fare(b['fare'])
            b['ride_date'] = str(b['ride_date'])
            b['ride_time'] = str(b['ride_time'])
            cur.close(); conn.close()
            return jsonify({'booking': b, 'picked': False})
        # Check if there was a recently accepted booking (picked by another driver)
        cur.execute(
            "SELECT id, accepted_by FROM Trip_Details WHERE status='Confirmed' AND accepted_by IS NOT NULL AND accepted_by != '' ORDER BY id DESC LIMIT 1"
        )
        picked = cur.fetchone()
        cur.close(); conn.close()
        if picked:
            return jsonify({'booking': None, 'picked': True, 'picked_by': picked[1]})
    return jsonify({'booking': None, 'picked': False})

@app.route('/driver-logout/<username>')
def driver_logout(username):
    drivers = session.get('drivers', {})
    drivers.pop(username, None)
    session.modified = True
    return redirect(url_for('driver_login'))

@app.route('/driver-home/<username>')
def driver_home(username):
    driver = get_driver(username)
    if not driver:
        return redirect(url_for('driver_login'))
    conn = get_db()
    booking = None
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Trip_Details WHERE status='Confirmed' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            booking = row_to_dict(cur, row)
            booking['fare']      = format_fare(booking['fare'])
            booking['ride_date'] = str(booking['ride_date'])
            booking['ride_time'] = str(booking['ride_time'])
        cur.close(); conn.close()
    return render_template('driver_home.html',
        booking      = booking,
        driver_name  = driver['username'],
        driver_photo = driver['photo'],
        driver_car   = driver['car'],
        driver_reg   = driver['reg']
    )

@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    trip_id = request.json.get('trip_id')
    otp     = request.json.get('otp')
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT otp FROM Trip_Details WHERE id=%s", (trip_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and str(row[0]) == str(otp):
            return jsonify({'valid': True})
        return jsonify({'valid': False})
    return jsonify({'valid': False})

@app.route('/api/skip-booking', methods=['POST'])
def api_skip_booking():
    trip_id     = request.json.get('trip_id')
    driver_name = request.json.get('driver_name')
    if trip_id and driver_name:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT IGNORE INTO Driver_Skipped_Trips (driver_name, trip_id) VALUES (%s,%s)", (driver_name, int(trip_id)))
            conn.commit()
            cur.close(); conn.close()
    return jsonify({'ok': True})

@app.route('/driver-cancel-trip', methods=['POST'])
def driver_cancel_trip():
    trip_id     = request.form.get('trip_id')
    driver_name = request.form.get('driver_name')
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE Trip_Details SET accepted_by=NULL WHERE id=%s", (trip_id,))
        cur.execute("INSERT IGNORE INTO Driver_Skipped_Trips (driver_name, trip_id) VALUES (%s,%s)", (driver_name, int(trip_id)))
        conn.commit()
        cur.close(); conn.close()
    return redirect(url_for('driver_home', username=driver_name))

@app.route('/accept-trip', methods=['POST'])
def accept_trip():
    trip_id     = request.form.get('trip_id')
    driver_name = request.form.get('driver_name', 'Unknown Driver')
    conn = get_db()
    booking = None
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE Trip_Details SET accepted_by=%s WHERE id=%s", (driver_name, trip_id))
        conn.commit()
        cur.execute("""
            SELECT t.id, t.pickup_location, t.drop_location, t.fare, t.distance_km,
                   r.username AS rider_name, r.mobile AS rider_mobile
            FROM Trip_Details t
            LEFT JOIN Rider_Details r ON r.id = t.rider_id
            WHERE t.id=%s
        """, (trip_id,))
        row = cur.fetchone()
        if row:
            booking = row_to_dict(cur, row)
            booking['fare'] = format_fare(booking['fare'])
        cur.close(); conn.close()
    return render_template('driver_accept.html', booking=booking, driver_name=driver_name)

@app.route('/start-trip/<username>')
def start_trip(username):
    driver = get_driver(username)
    if not driver:
        return redirect(url_for('driver_login'))
    conn = get_db()
    booking = None
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Trip_Details WHERE status='Confirmed' AND accepted_by=%s ORDER BY id DESC LIMIT 1", (username,))
        row = cur.fetchone()
        if row:
            booking = row_to_dict(cur, row)
            booking['fare']      = format_fare(booking['fare'])
            booking['ride_date'] = str(booking['ride_date'])
            booking['ride_time'] = str(booking['ride_time'])
        cur.close(); conn.close()
    return render_template('start_trip.html', booking=booking, username=username)

@app.route('/complete-trip', methods=['POST'])
def complete_trip():
    booking_id = request.form.get('booking_id')
    username   = request.form.get('username')
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE Trip_Details SET status='Completed' WHERE id=%s", (booking_id,))
        conn.commit()
        cur.close(); conn.close()
    return redirect(url_for('driver_home', username=username))

@app.route('/driver-profile')
def driver_profile():
    username = request.args.get('username', '')
    if not username:
        return redirect(url_for('driver_login'))
    conn = get_db()
    driver = None
    completed_trips = 0
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Driver_Details WHERE username=%s", (username,))
        row = cur.fetchone()
        if row:
            driver = row_to_dict(cur, row)
        cur.execute("SELECT COUNT(*) FROM Trip_Details WHERE accepted_by=%s AND status='Completed'", (username,))
        completed_trips = cur.fetchone()[0]
        cur.close(); conn.close()
    if not driver:
        return redirect(url_for('driver_login'))
    return render_template('driver_profile.html', driver=driver, completed_trips=completed_trips)

@app.route('/update-driver-profile', methods=['POST'])
def update_driver_profile():
    username = request.form.get('username')
    if not username:
        return redirect(url_for('driver_login'))
    
    conn = get_db()
    if conn:
        cur = conn.cursor()
        
        # Handle profile photo upload
        profile_photo = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename:
                profile_photo = save_file(file, f"{secure_filename(username)}_profile")
        
        # Update only profile photo
        if profile_photo:
            cur.execute(
                "UPDATE Driver_Details SET profile_photo=%s WHERE username=%s",
                (profile_photo, username)
            )
            conn.commit()
            
            # Update session cache
            drivers = session.get('drivers', {})
            if username in drivers:
                drivers[username]['photo'] = profile_photo
                session.modified = True
        
        cur.close(); conn.close()
    
    return redirect(url_for('driver_profile', username=username))

@app.route('/driver-earnings')
def driver_earnings():
    username = request.args.get('username', '')
    driver = get_driver(username)
    if not driver:
        return redirect(url_for('driver_login'))
    conn = get_db()
    trips = []
    daily = weekly = monthly = total = 0.0
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, r.username AS rider_name,
                   CURDATE() AS today,
                   DATEDIFF(CURDATE(), DATE(t.ride_date)) AS days_ago
            FROM Trip_Details t
            LEFT JOIN Rider_Details r ON r.id = t.rider_id
            WHERE t.status='Completed' AND t.accepted_by=%s
            ORDER BY t.id DESC
        """, (username,))
        for row in cur.fetchall():
            t = row_to_dict(cur, row)
            fare_val = parse_fare(str(t['fare']))
            t['fare_val'] = fare_val
            t['fare']      = format_fare(t['fare'])
            t['ride_date'] = str(t['ride_date'])
            t['ride_time'] = str(t['ride_time'])
            days_ago = t.get('days_ago', 999)
            if days_ago == 0:  daily   += fare_val
            if days_ago <= 6:  weekly  += fare_val
            if days_ago <= 29: monthly += fare_val
            total += fare_val
            trips.append(t)
        cur.close(); conn.close()
    return render_template('driver_earnings.html',
        driver_name     = username,
        driver_photo    = driver['photo'],
        trips           = trips,
        total_earnings  = f"\u20b9{total:,.2f}",
        daily_earnings  = f"\u20b9{daily:,.2f}",
        weekly_earnings = f"\u20b9{weekly:,.2f}",
        monthly_earnings= f"\u20b9{monthly:,.2f}"
    )

@app.route('/api/earnings-data/<username>')
def api_earnings_data(username):
    period = request.args.get('period', 'all')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    driver = get_driver(username)
    if not driver:
        return jsonify({'error': 'Driver not found'})
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'})
    
    # Build date filter based on period
    date_filter = ""
    params = [username]
    
    if period == 'today':
        date_filter = "AND DATE(t.ride_date) = CURDATE()"
    elif period == 'week':
        date_filter = "AND t.ride_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif period == 'month':
        date_filter = "AND MONTH(t.ride_date) = MONTH(CURDATE()) AND YEAR(t.ride_date) = YEAR(CURDATE())"
    elif period == 'year':
        date_filter = "AND YEAR(t.ride_date) = YEAR(CURDATE())"
    elif from_date and to_date:
        date_filter = "AND DATE(t.ride_date) BETWEEN %s AND %s"
        params.extend([from_date, to_date])
    
    cur = conn.cursor()
    cur.execute(f"""
        SELECT t.*, r.username AS rider_name
        FROM Trip_Details t
        LEFT JOIN Rider_Details r ON r.id = t.rider_id
        WHERE t.status='Completed' AND t.accepted_by=%s {date_filter}
        ORDER BY t.ride_date DESC, t.ride_time DESC
    """, params)
    
    trips = []
    total_earnings = 0
    trip_count = 0
    
    for row in cur.fetchall():
        t = row_to_dict(cur, row)
        fare_val = parse_fare(str(t['fare']))
        t['fare'] = format_fare(t['fare'])
        t['ride_date'] = str(t['ride_date'])
        t['ride_time'] = str(t['ride_time'])
        total_earnings += fare_val
        trip_count += 1
        trips.append(t)
    
    cur.close(); conn.close()
    
    return jsonify({
        'trips': trips,
        'total_earnings': f"\u20b9{total_earnings:,.2f}",
        'trip_count': trip_count,
        'average_fare': f"\u20b9{(total_earnings/trip_count if trip_count > 0 else 0):,.2f}"
    })

@app.route('/driver-trips')
def driver_trips():
    username = request.args.get('username', '')
    driver = get_driver(username)
    if not driver:
        return redirect(url_for('driver_login'))
    conn = get_db()
    trips = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, r.username AS rider_name
            FROM Trip_Details t
            LEFT JOIN Rider_Details r ON r.id = t.rider_id
            WHERE t.status='Completed' AND t.accepted_by=%s
            ORDER BY t.id DESC
        """, (username,))
        for row in cur.fetchall():
            t = row_to_dict(cur, row)
            t['fare'] = format_fare(t['fare'])
            t['ride_date'] = str(t['ride_date'])
            t['ride_time'] = str(t['ride_time'])
            trips.append(t)
        cur.close(); conn.close()
    return render_template('driver_trips.html', driver_name=username, trips=trips)


# ── Booking ──────────────────────────────────────────────────

@app.route('/driver-info/<username>/<int:booking_id>')
def driver_info(username, booking_id):
    rider_id = get_rider_id(username)
    if not rider_id:
        return redirect(url_for('rider_login'))
    conn = get_db()
    driver = None
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.pickup_location, t.drop_location, t.accepted_by,
                   d.mobile AS driver_mobile, d.car_make AS driver_car_make,
                   d.car_model AS driver_car_model, d.reg_number AS driver_reg,
                   d.car_color AS driver_car_color
            FROM Trip_Details t
            LEFT JOIN Driver_Details d ON d.username = t.accepted_by
            WHERE t.id=%s AND t.rider_id=%s
        """, (booking_id, rider_id))
        row = cur.fetchone()
        if row:
            driver = row_to_dict(cur, row)
        cur.close(); conn.close()
    if not driver or not driver.get('accepted_by'):
        return redirect(url_for('rider_bookings', username=username))
    return render_template('driver_info.html', driver=driver, rider_name=username)

@app.route('/rider-logout/<username>')
def rider_logout(username):
    riders = session.get('riders', {})
    riders.pop(username, None)
    session.modified = True
    return redirect(url_for('rider_login'))

@app.route('/book/<username>')
def book(username):
    if not get_rider_id(username):
        return redirect(url_for('rider_login'))
    mappls_key = os.environ.get('MAPPLS_KEY', 'zwcakbtliihnvvouvbsieoonjytfjadmunsv')
    return render_template('booking.html', username=username, mappls_key=mappls_key)

@app.route('/outstation/<username>')
def outstation(username):
    if not get_rider_id(username):
        return redirect(url_for('rider_login'))
    return render_template('outstation.html', username=username)

@app.route('/submit', methods=['POST'])
def submit():
    username  = request.form.get('username')
    rider_id  = get_rider_id(username)
    if not rider_id:
        return redirect(url_for('rider_login'))
    import re
    pickup    = re.sub(r'<[^>]*>', '', request.form.get('pickup', '')).strip()
    drop      = re.sub(r'<[^>]*>', '', request.form.get('drop', '')).strip()
    distance  = request.form.get('distance', '')
    fare_str  = request.form.get('fare', '')
    ride_date = request.form.get('ride_date', '')
    ride_time = request.form.get('ride_time', '')
    fare_val  = parse_fare(fare_str)
    otp       = str(random.randint(1000, 9999))
    try:
        dist_val = float(distance)
        if dist_val != dist_val or dist_val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return redirect(url_for('book', username=username))
    conn = get_db()
    order_id = None
    if conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Trip_Details (rider_id, pickup_location, drop_location, distance_km, fare, ride_date, ride_time, otp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (rider_id, pickup, drop, dist_val, fare_val, ride_date, ride_time, otp)
        )
        conn.commit()
        order_id = cur.lastrowid
        cur.close(); conn.close()
    riders_orders = session.setdefault('last_order', {})
    riders_orders[username] = order_id
    session.modified = True
    return redirect(url_for('rider_bookings', username=username))

@app.route('/clear-bookings', methods=['POST'])
def clear_bookings():
    username = request.form.get('username')
    rider_id = get_rider_id(username)
    if rider_id:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Trip_Details WHERE rider_id=%s AND status='Cancelled'", (rider_id,))
            conn.commit()
            cur.close(); conn.close()
    return redirect(url_for('rider_bookings', username=username))

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    booking_id = request.form.get('booking_id')
    username   = request.form.get('username')
    rider_id   = get_rider_id(username)
    if rider_id:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Trip_Details SET status='Cancelled' WHERE id=%s AND rider_id=%s AND status='Confirmed'",
                (booking_id, rider_id)
            )
            conn.commit()
            cur.close(); conn.close()
    return redirect(url_for('rider_bookings', username=username))

@app.route('/rider-bookings/<username>')
def rider_bookings(username):
    rider_id = get_rider_id(username)
    if not rider_id:
        return redirect(url_for('rider_login'))
    # Block suspended riders
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT account_status FROM Rider_Details WHERE id=%s", (rider_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and row[0] == 'Suspended':
            return render_template('rider_login.html', error='Your account has been suspended. Please contact support.')
    last_orders = session.get('last_order', {})
    order_id    = last_orders.pop(username, None)
    if order_id is not None:
        session.modified = True
    conn = get_db()
    bookings = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, d.mobile AS driver_mobile, d.car_make AS driver_car_make,
                   d.car_model AS driver_car_model, d.reg_number AS driver_reg,
                   d.car_color AS driver_car_color
            FROM Trip_Details t
            LEFT JOIN Driver_Details d ON d.username = t.accepted_by
            WHERE t.rider_id=%s ORDER BY t.id DESC
        """, (rider_id,))
        for row in cur.fetchall():
            b = row_to_dict(cur, row)
            raw_fare = float(b['fare'] or 0)
            b['fare']      = format_fare(raw_fare)
            b['ride_date'] = str(b['ride_date'])
            b['ride_time'] = str(b['ride_time'])
            b['otp']       = b.get('otp') or ''
            bookings.append(b)
        cur.close(); conn.close()
    return render_template('rider_bookings.html', bookings=bookings, order_id=order_id, rider_name=username)


# ════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ════════════════════════════════════════════════════════════

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        admin_user = os.environ.get('ADMIN_USER', 'shahirsd')
        admin_pass = os.environ.get('ADMIN_PASS', 'k7M#q9x2L')
        if request.form.get('user_id') == admin_user and request.form.get('password') == admin_pass:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid Admin ID or password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


def _load_admin_data():
    """Fetch all data needed by admin pages from MySQL."""
    conn = get_db()
    drivers, riders, trips = [], [], []
    if conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM Driver_Details ORDER BY id DESC")
        drivers = fetchall_dict(cur)

        cur.execute("SELECT * FROM Rider_Details ORDER BY id DESC")
        riders = fetchall_dict(cur)

        cur.execute("""
            SELECT t.*, r.username AS rider_name
            FROM Trip_Details t
            LEFT JOIN Rider_Details r ON r.id = t.rider_id
            ORDER BY t.id DESC
        """)
        rows = cur.fetchall()
        for row in rows:
            t = row_to_dict(cur, row)
            t['fare']        = format_fare(t['fare'])
            t['ride_date']   = str(t['ride_date'])
            t['ride_time']   = str(t['ride_time'])
            t['accepted_by'] = t.get('accepted_by') or '\u2014'
            trips.append(t)

        cur.close(); conn.close()

    # normalise field names for templates
    for d in drivers:
        d.setdefault('account_status', 'Active')
        d['registered_at'] = str(d.get('registered_at', ''))
    for r in riders:
        r.setdefault('account_status', 'Active')
        r['booking_count'] = 0
        r['registered_at'] = str(r.get('registered_at', ''))

    return drivers, riders, trips


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def safe_redirect(next_url, fallback):
    from urllib.parse import urlparse
    parsed = urlparse(next_url or '')
    if next_url and not parsed.scheme and not parsed.netloc:
        return redirect(next_url)
    return redirect(fallback)

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    drivers, riders, trips = _load_admin_data()
    completed = [t for t in trips if t.get('status') == 'Completed']
    confirmed = [t for t in trips if t.get('status') == 'Confirmed']
    search_data = (
        [{'type': 'Driver',  'name': d['username'], 'detail': f"{d['car_make']} {d['car_model']}", 'extra': d['reg_number']} for d in drivers] +
        [{'type': 'Rider',   'name': r['username'], 'detail': r['mobile'],  'extra': r['email']}  for r in riders] +
        [{'type': 'Booking', 'name': f"#{t['id']}", 'detail': t['pickup_location'], 'extra': t['drop_location']} for t in trips]
    )
    return render_template('admin_dashboard.html',
        drivers         = drivers,
        riders          = riders,
        total_drivers   = len(drivers),
        total_riders    = len(riders),
        total_trips     = len(trips),
        completed_trips = len(completed),
        active_bookings = len(confirmed),
        recent_bookings = trips[:10],
        search_data     = search_data
    )


@app.route('/admin-drivers')
@admin_required
def admin_drivers():
    drivers, _, trips = _load_admin_data()
    completed = [t for t in trips if t.get('status') == 'Completed']
    confirmed = [t for t in trips if t.get('status') == 'Confirmed']
    total_fare = sum(parse_fare(t['fare']) for t in completed)
    return render_template('admin_drivers.html',
        drivers         = drivers,
        all_bookings    = trips,
        completed_trips = len(completed),
        active_trips    = len(confirmed),
        total_revenue   = f'₹{total_fare:,.0f}'
    )


@app.route('/admin-riders')
@admin_required
def admin_riders():
    _, riders, trips = _load_admin_data()
    completed = [t for t in trips if t.get('status') == 'Completed']
    confirmed = [t for t in trips if t.get('status') == 'Confirmed']
    return render_template('admin_riders.html',
        riders             = riders,
        all_bookings       = trips,
        total_bookings     = len(trips),
        active_bookings    = len(confirmed),
        completed_bookings = len(completed)
    )


@app.route('/admin-toggle-driver', methods=['POST'])
@admin_required
def admin_toggle_driver():
    driver_id = int(request.form.get('driver_id'))
    action    = request.form.get('action')
    new_status = 'Suspended' if action == 'suspend' else 'Active'
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE Driver_Details SET account_status=%s WHERE id=%s", (new_status, driver_id))
        conn.commit()
        cur.close(); conn.close()
    return safe_redirect(request.form.get('next'), url_for('admin_dashboard'))


@app.route('/admin-toggle-rider', methods=['POST'])
@admin_required
def admin_toggle_rider():
    rider_id  = int(request.form.get('rider_id'))
    action    = request.form.get('action')
    new_status = 'Suspended' if action == 'suspend' else 'Active'
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE Rider_Details SET account_status=%s WHERE id=%s", (new_status, rider_id))
        conn.commit()
        cur.close(); conn.close()
    return safe_redirect(request.form.get('next'), url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
