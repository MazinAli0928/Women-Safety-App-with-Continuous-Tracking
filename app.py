import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Contact, AlertHistory, LocationUpdate
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from twilio.rest import Client

load_dotenv()

app = Flask(__name__)
# Generate a random secret key for session security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///women_safety.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone_number')
        
        # Validation
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email, phone_number=phone)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    recent_alerts = AlertHistory.query.filter_by(user_id=current_user.id).order_by(AlertHistory.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html', user=current_user, contacts=contacts, recent_alerts=recent_alerts)

@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    name = request.form.get('name')
    phone = request.form.get('phone_number')
    email = request.form.get('email')
    
    if name and phone:
        new_contact = Contact(name=name, phone_number=phone, email=email, user_id=current_user.id)
        db.session.add(new_contact)
        db.session.commit()
        flash('Emergency contact added successfully.', 'success')
    else:
        flash('Name and phone number are required.', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id == current_user.id:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/sos', methods=['POST'])
@login_required
def trigger_sos():
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    # 1. Log the alert
    new_alert = AlertHistory(user_id=current_user.id, latitude=lat, longitude=lng, status="Triggered")
    db.session.add(new_alert)
    db.session.commit()
    
    # Save initial location update
    if lat and lng:
        initial_loc = LocationUpdate(alert_id=new_alert.id, latitude=lat, longitude=lng)
        db.session.add(initial_loc)
        db.session.commit()
    
    # 2. Get contacts
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    
    tracking_url = request.host_url.rstrip('/') + url_for('track_live', alert_id=new_alert.id)
    
    # 3. Send actual alerts
    print(f"--- SOS TRIGGERED BY {current_user.username} ---")
    
    def send_email_alert(to_email, username, tracking_url):
        sender = os.getenv('EMAIL_SENDER')
        password = os.getenv('EMAIL_PASSWORD')
        if not sender or not password:
            print("Email credentials not set. Skipping email.")
            return False
        try:
            msg = EmailMessage()
            msg['Subject'] = f"EMERGENCY SOS from {username}"
            msg['From'] = sender
            msg['To'] = to_email
            msg.set_content(f"EMERGENCY ALERT\n\n{username} has triggered an SOS alert.\nTrack their live location here: {tracking_url}\n\nPlease contact them immediately or dispatch emergency services.")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def send_sms_alert(to_phone, username, tracking_url):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_phone = os.getenv('TWILIO_PHONE_NUMBER')
        if not account_sid or not auth_token or not from_phone:
            print("Twilio credentials not set. Skipping SMS.")
            return False
        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"EMERGENCY SOS: {username} has triggered an alert! Track live: {tracking_url}",
                from_=from_phone,
                to=to_phone
            )
            return True
        except Exception as e:
            print(f"Failed to send SMS to {to_phone}: {e}")
            return False

    sent_count = 0
    for contact in contacts:
        if contact.phone_number:
            print(f"Attempting to send SMS to {contact.phone_number}...")
            if send_sms_alert(contact.phone_number, current_user.username, tracking_url):
                sent_count += 1
        if contact.email:
            print(f"Attempting to send Email to {contact.email}...")
            if send_email_alert(contact.email, current_user.username, tracking_url):
                sent_count += 1
                
    print("--- END SOS ---")
    
    new_alert.status = "Sent" if sent_count > 0 else "Failed (Check Credentials)"
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'alert_id': new_alert.id,
        'message': f'SOS Alert triggered. Successfully sent {sent_count} real notifications.' if sent_count > 0 else 'SOS Logged (Credentials needed to send real alerts).'
    })

@app.route('/api/sos/update', methods=['POST'])
@login_required
def update_location():
    data = request.get_json()
    alert_id = data.get('alert_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if alert_id and lat and lng:
        loc = LocationUpdate(alert_id=alert_id, latitude=lat, longitude=lng)
        db.session.add(loc)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Missing data'}), 400

@app.route('/track/<int:alert_id>')
def track_live(alert_id):
    alert = AlertHistory.query.get_or_404(alert_id)
    return render_template('track.html', alert=alert)

@app.route('/api/track/<int:alert_id>')
def get_track_data(alert_id):
    alert = AlertHistory.query.get_or_404(alert_id)
    updates = LocationUpdate.query.filter_by(alert_id=alert_id).order_by(LocationUpdate.timestamp.asc()).all()
    coords = [{'lat': u.latitude, 'lng': u.longitude, 'time': u.timestamp.isoformat()} for u in updates]
    return jsonify({
        'username': alert.user.username,
        'status': alert.status,
        'coordinates': coords
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
