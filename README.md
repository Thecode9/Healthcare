# MedAI - Smart Healthcare & AI Symptom Diagnosis Platform

MedAI is a full-stack Progressive Web Application (PWA) designed to deliver accessible medical symptom assessment and clinical management. Powered by a Machine Learning classification engine trained on multi-symptom clinical data, MedAI provides patients with instant preliminary disease risk scores, recommended precautions, and medication guidance, alongside a dedicated Clinical Portal for healthcare professionals.

---

## Key Features

### 🩺 Patient Portal
- **AI Symptom Checker**: Multi-symptom input interface that processes symptom arrays through a trained **RandomForest Classifier** to generate ranked disease predictions with confidence scores.
- **Personalized Recommendations**: Automatic cross-referencing of predicted conditions with medication guidelines and medical precautions.
- **Consultation History**: Comprehensive log of past symptom assessments and diagnosis results.
- **Appointment Scheduling**: Online booking interface for scheduling clinical consultations with validation against past dates.
- **Health & Wellness Tips**: Daily rotating preventative healthcare advice and actionable wellness cards.
- **Patient Profile**: Comprehensive health profile management including blood type, allergies, and active medication tracking.

### 👨‍⚕️ Doctor Clinical Portal
- **Role-Based Access Control (RBAC)**: Restricted portal accessible strictly by authorized medical staff (`is_staff`).
- **Clinical Dashboard**: Real-time overview of pending appointments, today's consultations, and patient metrics.
- **Patient Record Management**: Searchable directory of registered patients with detailed medical history and past consultation summaries.
- **Appointment Workflow**: Direct status management (`PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED`) for scheduled patient appointments.

### 🔒 Security & Environment Architecture
- **Environment Isolation**: Sensitive configuration (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`) externalized via `.env` files with safe development fallbacks.
- **Git Security**: Comprehensive `.gitignore` protecting local database files, virtual environments, cache artifacts, and secret files from repository exposure.
- **Structured Logging**: Standardized Python logging system replacing raw console prints for production observability.

---

## Tech Stack

- **Backend Framework**: Django 6.0 (Python 3.12+)
- **Machine Learning**: `scikit-learn`, `joblib`, `pandas`, `numpy`
- **Frontend / PWA**: HTML5, Vanilla CSS3 (Custom Design System), JavaScript, Service Worker (Offline Support)
- **Database**: SQLite (Development) / PostgreSQL Compatible
- **Production Server**: Gunicorn + WhiteNoise (Static File Serving)

---

## Machine Learning Pipeline

1. **Dataset**: Multi-symptom disease classification matrix covering 41 distinct pathologies.
2. **Model Architecture**: `RandomForestClassifier` trained on binary symptom occurrence vectors.
3. **Inference Flow**:
   $$\text{Input Symptoms } S \longrightarrow \text{Feature Encoding } X \longrightarrow \text{RandomForest Probabilities } P(Y|X) \longrightarrow \text{Top-3 Rank Ordering}$$

---

## Quick Start & Installation

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-username/MedAi.git
cd MedAi

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```

### 4. Database Setup & Data Seeding
```bash
cd smart_healthcare_pwa

# Run database migrations
python manage.py migrate

# Seed medical database (Diseases, Symptoms, Medications, Precautions)
python seed_db.py
```

### 5. Create Superuser / Doctor Account
To access the Doctor Clinical Portal, create an administrative staff account:
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000` in your web browser.

---

## Running Automated Tests

MedAI includes a test suite covering models, patient view workflows, validation logic, and doctor authorization checks.

```bash
python manage.py test core
```

---

## Project Structure

```text
MedAi/
├── model_files/                  # Trained ML models and dataset CSVs
│   ├── random_forest_model.pkl   # Serialized RandomForest classifier
│   ├── model_columns.pkl         # Feature column alignment vector
│   ├── DiseaseAndSymptoms.csv    # Symptom-disease mapping dataset
│   ├── Disease precaution.csv    # Precaution guidelines dataset
│   └── metrics.py                # Dataset consistency verification utility
├── smart_healthcare_pwa/         # Django Web Application Root
│   ├── core/                     # Main Healthcare Application App
│   │   ├── models.py             # Domain Models (Disease, Symptom, Appointment, Profile)
│   │   ├── views.py              # Patient Portal View Handlers & ML Inference Engine
│   │   ├── doctor_views.py       # Doctor Clinical Portal Handlers
│   │   ├── tests.py              # Automated Test Suite
│   │   ├── templates/            # HTML5 PWA Templates
│   │   └── static/               # CSS, JS, Service Worker, and Manifest Assets
│   ├── smart_healthcare/         # Django Project Settings & Routing
│   │   └── settings.py           # Secured Environment Settings
│   ├── seed_db.py                # Database Seeding Utility Script
│   └── manage.py                 # Django CLI Tool
├── .env.example                  # Environment Variables Template
├── .gitignore                    # Git Exclusion Specifications
├── Procfile                      # Deployment Specification (Gunicorn)
├── requirements.txt              # Python Dependency Manifest
└── README.md                     # Project Documentation
```

---

## License & Disclaimer

**Disclaimer**: MedAI is designed as an educational and decision-support tool. It is not a replacement for professional medical diagnosis, advice, or treatment. Always seek the advice of a qualified healthcare provider with any medical questions.
