from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
import os, json, uuid, hashlib, datetime, io, base64
from werkzeug.utils import secure_filename
from ml_model import MedicalAIModel
from pdf_generator import generate_medical_pdf

app = Flask(__name__)
app.secret_key = 'medai_secret_key_2024_secure'
UPLOAD_FOLDER = 'static/uploads'
REPORTS_FOLDER = 'static/reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# Simple file-based user storage
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

ai_model = MedicalAIModel()

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        users = load_users()
        if email in users and users[email]['password'] == hash_password(password):
            session['user'] = email
            session['name'] = users[email]['name']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid email or password'})
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'patient')
        users = load_users()
        if email in users:
            return jsonify({'success': False, 'message': 'Email already registered'})
        users[email] = {
            'name': name,
            'password': hash_password(password),
            'role': role,
            'created': datetime.datetime.now().isoformat(),
            'reports': []
        }
        save_users(users)
        session['user'] = email
        session['name'] = name
        return jsonify({'success': True})
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('signin'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('signin'))
    users = load_users()
    user_data = users.get(session['user'], {})
    reports = user_data.get('reports', [])
    return render_template('dashboard.html', name=session['name'], reports=reports, email=session['user'])

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 'user' not in session:
        return redirect(url_for('signin'))
    if request.method == 'GET':
        return render_template('analyze.html', name=session['name'])

    # Collect patient data
    patient_data = {
        'name': request.form.get('patient_name', 'Unknown'),
        'age': int(request.form.get('age', 30)),
        'gender': request.form.get('gender', 'Unknown'),
        'symptoms': request.form.get('symptoms', ''),
        'blood_pressure': request.form.get('blood_pressure', '120/80'),
        'heart_rate': int(request.form.get('heart_rate', 72)),
        'temperature': float(request.form.get('temperature', 98.6)),
        'oxygen_saturation': int(request.form.get('oxygen_saturation', 98)),
        'glucose': int(request.form.get('glucose', 100)),
        'cholesterol': int(request.form.get('cholesterol', 180)),
        'weight': float(request.form.get('weight', 70)),
        'height': float(request.form.get('height', 170)),
        'medical_history': request.form.get('medical_history', ''),
        'medications': request.form.get('medications', ''),
        'allergies': request.form.get('allergies', ''),
        'report_date': datetime.datetime.now().strftime('%B %d, %Y'),
        'report_time': datetime.datetime.now().strftime('%H:%M'),
        'doctor_name': session['name'],
        'doctor_email': session['user']
    }

    # Handle image upload
    image_path = None
    image_analysis = None
    if 'medical_image' in request.files:
        file = request.files['medical_image']
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)
            image_analysis = ai_model.analyze_image(image_path)

    # Run AI analysis
    ai_result = ai_model.predict(patient_data)

    # Generate PDF
    report_id = str(uuid.uuid4())[:8].upper()
    pdf_filename = f"report_{report_id}.pdf"
    pdf_path = os.path.join(REPORTS_FOLDER, pdf_filename)

    generate_medical_pdf(patient_data, ai_result, image_analysis, image_path, pdf_path, report_id)

    # Save report reference to user
    users = load_users()
    report_entry = {
        'id': report_id,
        'patient': patient_data['name'],
        'date': patient_data['report_date'],
        'diagnosis': ai_result.get('primary_diagnosis', 'General Assessment'),
        'risk': ai_result.get('risk_level', 'Low'),
        'filename': pdf_filename
    }
    users[session['user']]['reports'] = users[session['user']].get('reports', [])
    users[session['user']]['reports'].insert(0, report_entry)
    save_users(users)

    return jsonify({
        'success': True,
        'report_id': report_id,
        'pdf_url': f'/download/{pdf_filename}',
        'diagnosis': ai_result.get('primary_diagnosis'),
        'risk': ai_result.get('risk_level'),
        'confidence': ai_result.get('confidence')
    })

@app.route('/download/<filename>')
def download(filename):
    if 'user' not in session:
        return redirect(url_for('signin'))
    path = os.path.join(REPORTS_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=filename)
    return "File not found", 404

@app.route('/view_report/<filename>')
def view_report(filename):
    if 'user' not in session:
        return redirect(url_for('signin'))
    path = os.path.join(REPORTS_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, mimetype='application/pdf')
    return "Not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
