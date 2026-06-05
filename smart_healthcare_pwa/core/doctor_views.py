import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Appointment, ConsultationHistory


def is_doctor(user):
    """Check if user is staff (doctor/admin)."""
    return user.is_staff


def doctor_login_view(request):
    """Separate login portal specifically for Doctors/Staff."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('doctor_dashboard')
        else:
            return redirect('dashboard')
            
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_staff:
                    login(request, user)
                    request.session['show_welcome_animation'] = True
                    messages.success(request, f"Clinical session initialized for Dr. {username}.")
                    return redirect('doctor_dashboard')
                else:
                    messages.error(request, "Access Denied: This portal is restricted to clinical staff only.")
            else:
                messages.error(request, "Invalid clinical credentials.")
        else:
            messages.error(request, "Invalid clinical credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/doctor/doctor_login.html', {'form': form})


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def doctor_dashboard(request):
    today = timezone.now().date()
    pending_count = Appointment.objects.filter(status='PENDING').count()
    confirmed_count = Appointment.objects.filter(status='CONFIRMED').count()
    patient_count = User.objects.filter(is_staff=False, is_superuser=False).count()
    today_consultations = ConsultationHistory.objects.filter(
        created_at__date=today
    ).count()

    recent_appointments = Appointment.objects.all().order_by('-created_at')[:5]
    recent_consultations = ConsultationHistory.objects.all().order_by('-created_at')[:5]

    show_welcome = request.session.pop('show_welcome_animation', False)

    return render(request, 'core/doctor/doctor_dashboard.html', {
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'patient_count': patient_count,
        'today_consultations': today_consultations,
        'recent_appointments': recent_appointments,
        'recent_consultations': recent_consultations,
        'show_welcome': show_welcome,
    })


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def doctor_appointments(request):
    appointments = Appointment.objects.all().order_by('-created_at')
    return render(request, 'core/doctor/doctor_appointments.html', {
        'appointments': appointments,
    })


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def doctor_update_appointment(request, appointment_id, new_status):
    appt = get_object_or_404(Appointment, id=appointment_id)
    valid_statuses = ['CONFIRMED', 'COMPLETED', 'CANCELLED']
    if new_status in valid_statuses:
        appt.status = new_status
        appt.save()
        messages.success(request, f"Appointment #{appt.id} marked as {new_status}.")
    return redirect('doctor_appointments')


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def doctor_patients(request):
    patients = User.objects.filter(
        is_staff=False, is_superuser=False
    ).select_related('userprofile').order_by('-date_joined')
    return render(request, 'core/doctor/doctor_patients.html', {
        'patients': patients,
    })


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def doctor_consultations(request):
    consultations = ConsultationHistory.objects.all().order_by('-created_at')
    return render(request, 'core/doctor/doctor_consultations.html', {
        'consultations': consultations,
    })


@login_required
@user_passes_test(is_doctor, login_url='doctor_login')
def patient_detail(request, user_id):
    """Full patient record view for doctors: profile + history + appointments."""
    patient = get_object_or_404(User, id=user_id, is_staff=False, is_superuser=False)

    consultations = ConsultationHistory.objects.filter(user=patient).order_by('-created_at')
    appointments = Appointment.objects.filter(user=patient).order_by('-appointment_date')

    # Enrich consultations with parsed predictions
    enriched = []
    for c in consultations:
        preds = []
        if c.predictions_json:
            try:
                preds = json.loads(c.predictions_json)
            except Exception:
                preds = []
        if not preds:
            preds = [{'rank': 1, 'disease': c.predicted_disease,
                      'probability': c.confidence_score,
                      'medication': c.recommended_medication or ''}]
        enriched.append({'consultation': c, 'predictions': preds})

    try:
        profile = patient.userprofile
    except Exception:
        profile = None

    return render(request, 'core/doctor/patient_detail.html', {
        'patient': patient,
        'profile': profile,
        'enriched': enriched,
        'appointments': appointments,
        'total_consultations': consultations.count(),
        'total_appointments': appointments.count(),
    })
