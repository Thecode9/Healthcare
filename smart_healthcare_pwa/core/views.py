from pathlib import Path
import pickle
import json

import pandas as pd
import joblib
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Symptom, Disease, Medication, ConsultationHistory, Appointment

def _find_model_dir():
    candidates = [
        Path(__file__).resolve().parents[2] / "model_files",
        Path(__file__).resolve().parents[3] / "model_files",
        Path(__file__).resolve().parents[1] / "model_files",
        Path.cwd() / "model_files",
        Path.cwd().parent / "model_files",
    ]
    for c in candidates:
        if c.exists() and (c / "random_forest_model.pkl").exists():
            return c
    return Path(__file__).resolve().parents[2] / "model_files"

MODEL_DIR = _find_model_dir()
MODEL_FILE = MODEL_DIR / "random_forest_model.pkl"
MODEL_COLUMNS_FILE = MODEL_DIR / "model_columns.pkl"
SYMPTOM_CSV_FILE = MODEL_DIR / "DiseaseAndSymptoms.csv"
ALL_SYMPTOMS_FILE = MODEL_DIR / "all_symptoms.pkl"

_prediction_model = None
_prediction_columns = None
_symptom_choices = None
_precaution_data = None


def load_prediction_model():
    global _prediction_model, _prediction_columns
    if _prediction_model is not None and _prediction_columns is not None:
        return _prediction_model, _prediction_columns

    try:
        if MODEL_FILE.exists():
            _prediction_model = joblib.load(MODEL_FILE)
            _prediction_columns = list(joblib.load(MODEL_COLUMNS_FILE))
            print(f"[MedAI] Model loaded successfully from {MODEL_FILE}")
        else:
            print(f"[MedAI] Model file not found at {MODEL_FILE}")
            _prediction_model = None
            _prediction_columns = []
    except Exception as e:
        print(f"[MedAI] Error loading model: {e}")
        _prediction_model = None
        _prediction_columns = []

    return _prediction_model, _prediction_columns


def load_symptom_choices():
    global _symptom_choices
    if _symptom_choices is not None:
        return _symptom_choices

    symptom_names = set()
    if SYMPTOM_CSV_FILE.exists():
        try:
            df = pd.read_csv(SYMPTOM_CSV_FILE)
            symptom_columns = [col for col in df.columns if col.lower().startswith('symptom')]
            for col in symptom_columns:
                symptom_names.update(
                    df[col]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .tolist()
                )
        except Exception:
            symptom_names = set()

    if not symptom_names and ALL_SYMPTOMS_FILE.exists():
        try:
            with open(ALL_SYMPTOMS_FILE, 'rb') as f:
                symptom_names = set(pickle.load(f))
        except Exception:
            symptom_names = set()

    if not symptom_names:
        symptom_names = {sym.name.strip().lower() for sym in Symptom.objects.all()}

    symptom_names = {name for name in symptom_names if name and name.lower() != 'nan'}
    _symptom_choices = sorted(symptom_names)
    return _symptom_choices


def load_precaution_data():
    global _precaution_data
    if _precaution_data is not None:
        return _precaution_data

    _precaution_data = {}
    precaution_file = MODEL_DIR / "Disease precaution.csv"
    if precaution_file.exists():
        try:
            df = pd.read_csv(precaution_file)
            for _, row in df.iterrows():
                disease = str(row['Disease']).strip().lower()
                precautions = []
                for col in ['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']:
                    if col in df.columns and pd.notna(row[col]) and str(row[col]).strip():
                        precautions.append(str(row[col]).strip())
                _precaution_data[disease] = precautions
        except Exception:
            _precaution_data = {}
    return _precaution_data


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Please complete your profile.")
            return redirect('onboarding')
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['show_welcome_animation'] = True
                messages.info(request, f"You are now logged in as {username}.")
                # Redirect doctors to doctor portal
                if user.is_staff:
                    return redirect('doctor_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    is_staff = request.user.is_staff
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    if is_staff:
        return redirect('doctor_login')
    return redirect('login')

@login_required
def dashboard(request):
    import random
    from django.utils import timezone as tz
    show_welcome = request.session.pop('show_welcome_animation', False)

    # --- Last consultation & streak ---
    last_consult = ConsultationHistory.objects.filter(user=request.user).order_by('-created_at').first()
    days_since = None
    streak_status = 'none'
    if last_consult:
        delta = (tz.now() - last_consult.created_at).days
        days_since = delta
        if delta == 0:
            streak_status = 'today'
        elif delta <= 7:
            streak_status = 'recent'
        elif delta <= 30:
            streak_status = 'moderate'
        else:
            streak_status = 'overdue'

    # --- Daily health tip (cycles by day of year) ---
    daily_tips = [
        {'icon': '💧', 'text': 'Drink at least 8 glasses of water today to stay hydrated.'},
        {'icon': '😴', 'text': 'Aim for 7–9 hours of sleep tonight for peak recovery.'},
        {'icon': '🥦', 'text': 'Add at least one leafy green to your meals today.'},
        {'icon': '🚶', 'text': '30 minutes of walking today can boost your mood significantly.'},
        {'icon': '🧘', 'text': 'Take 5 deep breaths. Reducing stress protects your heart.'},
        {'icon': '🍎', 'text': 'Swap a processed snack for fresh fruit this afternoon.'},
        {'icon': '☀️', 'text': 'Get some sunlight today — 15 minutes supports your vitamin D.'},
    ]
    tip = daily_tips[tz.now().timetuple().tm_yday % len(daily_tips)]

    return render(request, 'core/dashboard.html', {
        'show_welcome': show_welcome,
        'last_consult': last_consult,
        'days_since': days_since,
        'streak_status': streak_status,
        'daily_tip': tip,
    })

@login_required
def symptom_checker(request):
    if request.method == 'POST':
        selected_symptom_names = [name.strip() for name in request.POST.getlist('symptoms') if name]

        if not selected_symptom_names:
            messages.error(request, "Please select at least one symptom.")
            return redirect('symptoms')

        model, model_columns = load_prediction_model()
        predicted_disease = None
        medication_names = "Please consult a doctor for proper diagnosis."
        top_predictions = []

        if model is not None and model_columns is not None and len(model_columns) > 0:
            try:
                input_data = {
                    col: 1 if col in selected_symptom_names else 0
                    for col in model_columns
                }
                input_df = pd.DataFrame([input_data], columns=model_columns)
                
                # Get probabilities for all classes
                probs = model.predict_proba(input_df)[0]
                classes = model.classes_
                
                # Zip classes and probabilities, sort descending
                class_probs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
                
                # Extract top 3 predictions
                for i, (disease, prob) in enumerate(class_probs[:3]):
                    disease_name = str(disease).strip()
                    # Lookup medication
                    d_obj = Disease.objects.filter(name__iexact=disease_name).first()
                    if d_obj:
                        medications = Medication.objects.filter(disease=d_obj)
                        meds_str = ", ".join([m.name for m in medications]) if medications.exists() else "No specific medication found. Please consult a doctor."
                    else:
                        meds_str = "No specific medication found. Please consult a doctor."
                    
                    top_predictions.append({
                        "rank": i + 1,
                        "disease": disease_name,
                        "probability": round(float(prob) * 100, 1),
                        "medication": meds_str
                    })
                
                if top_predictions:
                    predicted_disease = top_predictions[0]["disease"]
                    medication_names = top_predictions[0]["medication"]
            except Exception as e:
                import traceback
                print(f"[MedAI] Prediction error: {e}")
                traceback.print_exc()
                predicted_disease = None

        if not predicted_disease:
            predicted_disease = "No match found"

        # Save consultation to history
        history = ConsultationHistory.objects.create(
            user=request.user,
            predicted_disease=predicted_disease,
            confidence_score=top_predictions[0]["probability"] if top_predictions else 0.0,
            recommended_medication=medication_names,
            symptoms_reported=", ".join(selected_symptom_names),
            predictions_json=json.dumps(top_predictions) if top_predictions else None
        )
        return redirect('results', history_id=history.id)

    # Load symptoms from database (ground truth matching model columns)
    all_symptoms = Symptom.objects.all().order_by('name')
    return render(request, 'core/symptom_checker.html', {'symptoms': all_symptoms})

@login_required
def results_view(request, history_id):
    try:
        history = ConsultationHistory.objects.get(id=history_id, user=request.user)
    except ConsultationHistory.DoesNotExist:
        return redirect('dashboard')
        
    predictions = []
    if history.predictions_json:
        try:
            predictions = json.loads(history.predictions_json)
        except Exception:
            predictions = []
            
    if not predictions:
        predictions = [{
            "rank": 1,
            "disease": history.predicted_disease,
            "probability": 100.0,
            "medication": history.recommended_medication or "Please consult a doctor."
        }]
        
    return render(request, 'core/results.html', {
        'history': history,
        'predictions': predictions
    })

@login_required
def history_view(request):
    histories = ConsultationHistory.objects.filter(user=request.user).order_by('-created_at')
    appointments = Appointment.objects.filter(user=request.user).order_by('-appointment_date')
    return render(request, 'core/history.html', {'histories': histories, 'appointments': appointments})

@login_required
def book_appointment(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        reason = request.POST.get('reason')
        # Validate date format (ISO or YYYY-MM-DD) and ensure future date/time
        from datetime import datetime
        try:
            # Django date input returns 'YYYY-MM-DD' (no time). We'll assume 09:00 default if time missing
            appointment_dt = datetime.fromisoformat(date_str)
        except ValueError:
            try:
                appointment_dt = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception:
                messages.error(request, "Invalid date format. Please try again.")
                return redirect('book_appointment')
        now = datetime.now()
        if appointment_dt < now:
            messages.error(request, "You cannot book an appointment in the past. Choose a future date/time.")
            return redirect('book_appointment')
        Appointment.objects.create(
            user=request.user,
            appointment_date=appointment_dt,
            reason=reason,
            status='PENDING'
        )
        messages.success(request, "Appointment booked successfully!")
        return redirect('history')
    return render(request, 'core/appointment.html')

@login_required
def health_tips(request):
    tips = [
        {'icon': '💧', 'title': 'Stay Hydrated', 'body': 'Drink at least 8 glasses of water a day. Hydration helps your kidneys, skin, and brain function at their best.'},
        {'icon': '😴', 'title': 'Get Enough Sleep', 'body': 'Adults need 7–9 hours of sleep per night. Poor sleep is linked to a weakened immune system and increased stress.'},
        {'icon': '🥦', 'title': 'Eat More Vegetables', 'body': 'Aim for 5 portions of fruit and vegetables per day. They provide essential vitamins, minerals, and fibre.'},
        {'icon': '🚶', 'title': 'Stay Active', 'body': 'Even 30 minutes of walking per day can significantly reduce your risk of heart disease, diabetes, and depression.'},
        {'icon': '🧼', 'title': 'Wash Your Hands', 'body': 'Regular handwashing is one of the most effective ways to prevent the spread of infections and illnesses.'},
        {'icon': '🩺', 'title': 'Regular Check-ups', 'body': 'Visit a doctor at least once a year even if you feel fine. Early detection of problems leads to better outcomes.'},
    ]
    return render(request, 'core/health_tips.html', {'tips': tips})

@login_required
def disease_detail(request, disease_name):
    prob = request.GET.get('prob', 'N/A')
    if prob != 'N/A' and not str(prob).endswith('%'):
        prob = f"{prob}%"
        
    disease_info = {
        'name': disease_name,
        'probability': prob,
        'top_symptoms': [],
        'precautions': []
    }
    
    # 1. Fetch real precautions from database
    real_disease = Disease.objects.filter(name__iexact=disease_name).first()
    precautions = []
    if real_disease:
        precautions = [p.description for p in real_disease.precautions.all()]
        
    if not precautions:
        precautions = [
            'Drink plenty of fluids and rest',
            'Monitor symptoms closely',
            'Avoid spreading to others',
            'Seek medical attention if symptoms worsen'
        ]
    # Capitalize each precaution for beautiful rendering
    disease_info['precautions'] = [p.capitalize() for p in precautions]
    
    # 2. Fetch real symptoms from database
    try:
        real_disease = Disease.objects.filter(name__iexact=disease_name).first()
        if real_disease:
            disease_info['top_symptoms'] = [s.name.replace('_', ' ').title() for s in real_disease.symptoms.all()[:7]]
    except Exception:
        pass
        
    # Fallback to loading symptoms from DiseaseAndSymptoms.csv if database is empty
    if not disease_info['top_symptoms']:
        try:
            symptoms_set = set()
            csv_file = MODEL_DIR / "DiseaseAndSymptoms.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                df_match = df[df['Disease'].str.strip().str.lower() == disease_name.lower().strip()]
                symptom_cols = [c for c in df.columns if c.lower().startswith('symptom')]
                for _, row in df_match.iterrows():
                    for col in symptom_cols:
                        val = str(row[col]).strip().replace('_', ' ').title()
                        if val and val.lower() != 'nan':
                            symptoms_set.add(val)
            disease_info['top_symptoms'] = sorted(list(symptoms_set))[:7]
        except Exception:
            pass
            
    # Final fallback if still empty
    if not disease_info['top_symptoms']:
        disease_info['top_symptoms'] = ['Fever', 'Fatigue', 'Headache', 'Nausea', 'Restlessness']

    return render(request, 'core/disease_detail.html', {'disease': disease_info})

@login_required
def onboarding_view(request):
    # Check if user already has a profile
    from .models import UserProfile
    if hasattr(request.user, 'userprofile'):
        return redirect('dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        blood_type = request.POST.get('blood_type')
        actively_on_medication = request.POST.get('actively_on_medication') == 'on'
        current_medications = request.POST.get('current_medications')
        allergies = request.POST.get('allergies')

        UserProfile.objects.create(
            user=request.user,
            full_name=full_name,
            age=age,
            gender=gender,
            blood_type=blood_type,
            actively_on_medication=actively_on_medication,
            current_medications=current_medications,
            allergies=allergies
        )
        messages.success(request, "Profile created successfully!")
        return redirect('dashboard')
        
    return render(request, 'core/onboarding.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.userprofile
    except:
        # If they somehow skipped onboarding
        return redirect('onboarding')
        
    return render(request, 'core/profile.html', {'profile': profile})
