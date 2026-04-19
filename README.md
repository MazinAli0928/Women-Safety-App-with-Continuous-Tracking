# Web-Based Women Safety Application with GPS Tracking 🛡️

A comprehensive, full-stack safety application designed to help women in emergency situations. With a single click, users can instantly notify their trusted contacts with a live-updating map showing their real-time geographical location.

## Features ✨

- **One-Click SOS**: Instantly triggers an emergency workflow with a single prominent button.
- **Continuous Live Tracking**: Silently polls the device's GPS and draws a live path of the user's movements on a dedicated tracking page.
- **Real-Time Notifications**: Automatically dispatches both **Emails** (via SMTP) and **SMS text messages** (via Twilio) to all trusted contacts.
- **Contact Management**: Users can easily add, edit, and delete trusted family members and friends.
- **Secure Authentication**: Full user registration and login system with hashed passwords.
- **Premium UI/UX**: Dark-mode-first aesthetic with smooth micro-animations, glassmorphism, and responsive design.

## Tech Stack 🛠️

- **Frontend**: Vanilla HTML5, CSS3, JavaScript, Leaflet.js (for map rendering).
- **Backend**: Python, Flask, Flask-Login, Flask-SQLAlchemy.
- **Database**: SQLite (Development)
- **External APIs**: Twilio API (SMS), Python `smtplib` (Email).

## Getting Started 🚀

### 1. Prerequisites
- Python 3.8+ installed on your machine.
- A free [Twilio](https://www.twilio.com/) account (if you wish to test SMS).
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833?hl=en) generated (if you wish to test Emails).

### 2. Installation
Clone the repository and set up a virtual environment:

```bash
git clone <your-repo-url>
cd women_safety_app
python -m venv venv
```

Activate the virtual environment:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

Install the required dependencies:
```bash
pip install -r requirements.txt
```
*(Note: If `requirements.txt` is missing, you can install the dependencies manually using: `pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug twilio python-dotenv`)*

### 3. Environment Variables
To enable SMS and Email alerts, copy the provided `.env.example` file and rename it to `.env`:
```bash
cp .env.example .env
```
Open the `.env` file and insert your API credentials. **Never commit your `.env` file to version control.**

### 4. Running the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## Future Enhancements 🔮
As outlined in the project synopsis, potential future upgrades include:
- Voice-Based SOS Activation ("Help me", "Emergency").
- Audio/Camera Evidence Recording.
- Gesture-Based Triggers (Device shaking).
- Direct Police/Ambulance dispatch integration.

## License 📄
This project was developed as an academic synopsis implementation. All rights reserved.
