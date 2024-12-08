from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import timedelta
from flask import flash
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from dotenv import load_dotenv
import re

from database import db  # Import db from database.py
from models import User

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.secret_key = 'SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Sample data for demonstration
alerts = [
    {"message": "Phishing attempt detected in your area. Stay vigilant!", "timestamp": "2024-11-12 19:42:05"}
]

incident_reports = [
    {"description": "Unauthorized access attempt", "timestamp": "2024-11-07"},
    {"description": "Suspicious email reported", "timestamp": "2024-11-06"}
]

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# Initialize Twilio client
client = Client(account_sid, auth_token)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    local_government = db.Column(db.String(100))
    community = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Threat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    threat_type = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def send_email(to_email, subject, content):
    message = Mail(
        from_email='your_email@example.com',
        to_emails=to_email,
        subject=subject,
        html_content=content)
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(str(e))

def send_sms(to_number, message):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            body=message,
            from_='+1234567890',  # Your Twilio phone number
            to=to_number
        )
        return f"Message sent: {message.sid}"
    except Exception as e:
        return f"Error: {str(e)}"

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

@app.before_request
def make_session_permanent():
    session.permanent = False

@app.route('/')
def home():
    return render('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('register'))
        
        if existing_email:
            flash('Email already exists. Please use a different email.')
            return redirect(url_for('register'))
        
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number,
            email=email,
            password=password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))
    
    return('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username  # Store username in session
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        threats = Threat.query.filter_by(user_id=user.id).all()
        return render_template('dashboard.html', user=user, threats=threats)
    elif 'username' in session:
        return f'Welcome to your dashboard, {session["username"]}!'
    return redirect(url_for('login'))

@app.route('/security')
def security():
    return render_template('security.html')

@app.route('/emergency')
def emergency():
    return render_template('emergency.html')

@app.route('/training')
def training():
    return render_template('training.html')

@app.route('/api/alerts')
def get_alerts():
    return jsonify(alerts)

@app.route('/api/incident-reports')
def get_incident_reports():
    return jsonify(incident_reports)

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user_id' in session:
        if request.method == 'POST':
            threat_type = request.form['threat_type']
            description = request.form['description']
            new_threat = Threat(user_id=session['user_id'], threat_type=threat_type, description=description)
            db.session.add(new_threat)
            db.session.commit()
            # Send notification (email/SMS)
            send_email('recipient@example.com', 'New Threat Reported', f'Threat Type: {threat_type}\nDescription: {description}')
            send_sms('+1234567890', f'New Threat Reported: {threat_type}')
            flash('Threat reported successfully!')
            return redirect(url_for('dashboard'))
        return render_template('report.html')
    return redirect(url_for('login'))

@app.route('/send_sms', methods=['POST'])
def send_sms_route():
    data = request.get_json()
    to_number = data.get('to_number')
    message_body = data.get('message')
    result = send_sms(to_number, message_body)
    return jsonify({'result': result})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
