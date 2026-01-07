from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "rtv_secure_key"

# 1. Firebase Setup
# Oboshoyi tomar key.json file-er path thik thakbe
firebase_config = {
    "type": "service_account",
    "project_id": os.environ["FIREBASE_PROJECT_ID"],
    "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
    "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
    "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
    "client_id": os.environ["FIREBASE_CLIENT_ID"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"]
}

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()
 # If you are using Firestore


# --- Login logic ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "admin123": 
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash("Wrong Password!", "danger")
    return render_template('login.html')

# --- Home / Dashboard ---
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Firebase theke data ana
    p_ref = db.collection('Patients').stream()
    all_p = [doc.to_dict() for doc in p_ref]
    
    # Critical vs Normal filter
    crit = [p for p in all_p if p.get('condition') == 'Critical']
    norm = [p for p in all_p if p.get('condition') != 'Critical']
    
    docs = [doc.to_dict() for doc in db.collection('Doctors').stream()]
    inventory = {"Paracetamol": 50, "Insulin": 20}
    
    return render_template('index.html', critical=crit, normal=norm, doctors=docs, inventory=inventory)

# --- Logic: Patient Admission ---
@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form.get('name')
    phone = request.form.get('phone')
    adm = request.form.get('adm_date')
    dis = request.form.get('dis_date')
    cond = request.form.get('condition')
    
    try:
        days = (datetime.strptime(dis, '%Y-%m-%d') - datetime.strptime(adm, '%Y-%m-%d')).days
        bill = max(days, 1) * 1500
    except: bill = 1500

    db.collection('Patients').document(phone).set({
        'name': name, 'phone': phone, 'adm': adm, 'dis': dis, 'bill': bill, 'condition': cond
    })
    return redirect(url_for('home'))

# --- Logic: Doctor Registration ---
@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    d_name = request.form.get('doc_name')
    spec = request.form.get('specialty')
    stat = request.form.get('status')
    db.collection('Doctors').document(d_name).set({
        'name': d_name, 'specialty': spec, 'status': stat
    })
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

