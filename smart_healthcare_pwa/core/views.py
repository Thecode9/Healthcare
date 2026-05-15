from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Symptom, Disease, Medication, ConsultationHistory, Appointment

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
            messages.success(request, "Registration successful.")
            return redirect('dashboard')
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
        selected_symptom_names = request.POST.getlist('symptoms')

        if not selected_symptom_names:
            messages.error(request, "Please select at least one symptom.")
            return redirect('symptoms')

        # --- RULE-BASED PREDICTION ENGINE ---
        # Get selected symptom objects from the database
        selected_symptoms = Symptom.objects.filter(name__in=selected_symptom_names)

        # Score each disease by how many of its symptoms match the selected ones
        best_match = None
        best_score = 0

        for disease in Disease.objects.all():
            disease_symptoms = disease.symptoms.all()
            match_count = disease_symptoms.filter(id__in=selected_symptoms).count()
            if match_count > best_score:
                best_score = match_count
                best_match = disease

        if best_match and best_score > 0:
            predicted_disease = best_match.name
            # Fetch recommended medications for this disease
            medications = Medication.objects.filter(disease=best_match)
            medication_names = ", ".join([m.name for m in medications]) if medications.exists() else "No specific medication found. Please consult a doctor."
        else:
            predicted_disease = "No match found"
            medication_names = "Please consult a doctor for proper diagnosis."

        # Save consultation to history
        history = ConsultationHistory.objects.create(
            user=request.user,
            predicted_disease=predicted_disease,
            recommended_medication=medication_names,
            symptoms_reported=", ".join(selected_symptom_names)
        )
        return redirect('results', history_id=history.id)

    # Load all symptoms from database for the form
    all_symptoms = Symptom.objects.all().order_by('name')
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
