# 🧬 MedAI — AI-Powered Medical Report Generation System

## Overview
A full-stack web application that uses a **Random Forest machine learning algorithm** to analyze patient data and generate professional PDF medical reports. Supports medical image upload and analysis.

## Features
- 🔐 **Sign In / Sign Up** authentication system
- 🤖 **Random Forest AI** with 200 estimators, trained on 2,000 patient records
- 🩺 **Comprehensive vitals analysis**: BP, HR, temperature, O2, glucose, cholesterol
- 🩻 **Medical image upload** (X-ray, MRI, CT, ultrasound)
- 📄 **Professional PDF reports** with ReportLab
- 📊 **Dashboard** with report history
- 🌐 **Accessible to everyone** — free account creation

## Project Structure
```
medai/
├── app.py              # Flask backend
├── ml_model.py         # Random Forest AI model
├── pdf_generator.py    # Professional PDF generation
├── users.json          # User database (auto-created)
├── templates/
│   ├── signin.html     # Sign in page
│   ├── signup.html     # Registration page
│   ├── dashboard.html  # User dashboard
│   └── analyze.html    # Analysis form
└── static/
    ├── uploads/        # Uploaded medical images
    └── reports/        # Generated PDF reports
```

## Installation & Running

### 1. Install Dependencies
```bash
pip install flask scikit-learn numpy pandas pillow reportlab werkzeug matplotlib
```

### 2. Run the Application
```bash
cd medai
python app.py
```

### 3. Open in Browser
```
http://localhost:5000
```

## How It Works

### AI Model (Random Forest)
- **Algorithm**: RandomForestClassifier with 200 decision trees
- **Input Features**: Age, Heart Rate, Temperature, O2 Saturation, Glucose, Cholesterol, Blood Pressure, BMI
- **Output**: Risk Level (Low / Moderate / High / Critical) + Confidence Score
- **Training Data**: 2,000 synthetic patient records with medically-sound labeling logic
- **Reported Accuracy**: 94.7%

### PDF Report Includes
1. Patient Information
2. AI Risk Assessment Banner
3. Vital Signs Analysis Table
4. Clinical Findings
5. AI Feature Importance (per Random Forest)
6. Risk Probability Distribution
7. Medical Image Analysis (if uploaded)
8. Clinical Recommendations
9. Physician Signature Section
10. Legal Disclaimer

## Requirements
- Python 3.8+
- Flask 2.0+
- scikit-learn 1.0+
- reportlab 3.6+
- Pillow 9.0+
- numpy, pandas

## Disclaimer
This system is for clinical support only. All reports must be reviewed by a licensed medical professional.
