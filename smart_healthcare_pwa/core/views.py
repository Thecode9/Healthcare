from pathlib import Path
import pickle

import pandas as pd
import joblib
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Symptom, Disease, Medication, ConsultationHistory, Appointment

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
# prefer model files inside Healthcare/model_files so the app is self-contained
LOCAL_MODEL_DIR = WORKSPACE_ROOT / "model_files"
# fallback to repo-level model_files (one directory up) for existing files
REPO_MODEL_DIR = Path(__file__).resolve().parents[4] / "model_files"

def _choose_model_path(filename):
    local = LOCAL_MODEL_DIR / filename
    repo = REPO_MODEL_DIR / filename
    if local.exists():
        return local
    return repo

MODEL_FILE = _choose_model_path("random_forest_model.pkl")
MODEL_COLUMNS_FILE = _choose_model_path("model_columns.pkl")
SYMPTOM_CSV_FILE = _choose_model_path("DiseaseAndSymptoms.csv")
ALL_SYMPTOMS_FILE = _choose_model_path("all_symptoms.pkl")

_prediction_model = None
_prediction_columns = None
_symptom_choices = None


def load_prediction_model():
    global _prediction_model, _prediction_columns
    if _prediction_model is not None and _prediction_columns is not None:
        return _prediction_model, _prediction_columns

    try:
        _prediction_model = joblib.load(MODEL_FILE)
        _prediction_columns = list(joblib.load(MODEL_COLUMNS_FILE))
    except Exception:
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
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

@login_required
def symptom_checker(request):
    if request.method == 'POST':
        selected_symptom_names = [name.strip().lower() for name in request.POST.getlist('symptoms') if name]

        if not selected_symptom_names:
            messages.error(request, "Please select at least one symptom.")
            return redirect('symptoms')

        model, model_columns = load_prediction_model()
        predicted_disease = None
        medication_names = "Please consult a doctor for proper diagnosis."

        if model is not None and model_columns is not None and len(model_columns) > 0:
            try:
                input_data = {
                    col: 1 if col in selected_symptom_names else 0
                    for col in model_columns
                }
                input_df = pd.DataFrame([input_data], columns=model_columns)
                predicted_disease = model.predict(input_df)[0]
                predicted_disease = str(predicted_disease).strip()
            except Exception:
                predicted_disease = None

        if not predicted_disease:
            predicted_disease = "No match found"
        else:
            disease_obj = Disease.objects.filter(name__iexact=predicted_disease).first()
            if disease_obj:
                medications = Medication.objects.filter(disease=disease_obj)
                medication_names = ", ".join([m.name for m in medications]) if medications.exists() else "No specific medication found. Please consult a doctor."
            else:
                medication_names = "No specific medication found. Please consult a doctor."

        # Save consultation to history
        history = ConsultationHistory.objects.create(
            user=request.user,
            predicted_disease=predicted_disease,
            recommended_medication=medication_names,
            symptoms_reported=", ".join(selected_symptom_names)
        )
        return redirect('results', history_id=history.id)

    # Load symptoms directly from the dataset for the form
    raw_symptoms = load_symptom_choices()
    all_symptoms = [
        {
            'key': symp,
            'label': symp.replace('_', ' ').title()
        }
        for symp in raw_symptoms
    ]
    return render(request, 'core/symptom_checker.html', {'symptoms': all_symptoms})

@login_required
def results_view(request, history_id):
    try:
        history = ConsultationHistory.objects.get(id=history_id, user=request.user)
    except ConsultationHistory.DoesNotExist:
        return redirect('dashboard')
        
    return render(request, 'core/results.html', {'history': history})

@login_required
def history_view(request):
    histories = ConsultationHistory.objects.filter(user=request.user).order_by('-created_at')
    appointments = Appointment.objects.filter(user=request.user).order_by('-appointment_date')
    return render(request, 'core/history.html', {'histories': histories, 'appointments': appointments})

@login_required
def book_appointment(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        reason = request.POST.get('reason')
        Appointment.objects.create(
            user=request.user,
            appointment_date=date,
            reason=reason,
            status='PENDING'
        )
        messages.success(request, "Emergency appointment booked successfully!")
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
    # Fallback mock data matching prototype if disease isn't fully set up yet
    disease_info = {
        'name': disease_name,
        'probability': request.GET.get('prob', 'N/A'),
        'top_symptoms': ['Fever', 'Chills', 'Sweating', 'Headache', 'Nausea', 'Vomiting', 'Fatigue'],
        'precautions': [
            'Drink plenty of fluids',
            'Rest and sleep well',
            'Take medication as advised',
            'Use mosquito repellent',
            'Seek medical attention if symptoms worsen'
        ]
    }
    
    # Try to fetch real symptoms if disease exists in DB
    try:
        real_disease = Disease.objects.get(name=disease_name)
        disease_info['top_symptoms'] = [s.name for s in real_disease.symptoms.all()[:7]]
    except Disease.DoesNotExist:
        pass

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
