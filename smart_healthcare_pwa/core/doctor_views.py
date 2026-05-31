from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Appointment, ConsultationHistory


def is_doctor(user):
    """Check if user is staff (doctor/admin)."""
    return user.is_staff


@login_required
@user_passes_test(is_doctor, login_url='login')
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

    return render(request, 'core/doctor/doctor_dashboard.html', {
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'patient_count': patient_count,
        'today_consultations': today_consultations,
        'recent_appointments': recent_appointments,
        'recent_consultations': recent_consultations,
    })


@login_required
@user_passes_test(is_doctor, login_url='login')
def doctor_appointments(request):
    appointments = Appointment.objects.all().order_by('-created_at')
    return render(request, 'core/doctor/doctor_appointments.html', {
        'appointments': appointments,
    })


@login_required
@user_passes_test(is_doctor, login_url='login')
def doctor_update_appointment(request, appointment_id, new_status):
    appt = get_object_or_404(Appointment, id=appointment_id)
    valid_statuses = ['CONFIRMED', 'COMPLETED', 'CANCELLED']
    if new_status in valid_statuses:
        appt.status = new_status
        appt.save()
        messages.success(request, f"Appointment #{appt.id} marked as {new_status}.")
    return redirect('doctor_appointments')


@login_required
@user_passes_test(is_doctor, login_url='login')
def doctor_patients(request):
    patients = User.objects.filter(
        is_staff=False, is_superuser=False
    ).select_related('userprofile').order_by('-date_joined')
    return render(request, 'core/doctor/doctor_patients.html', {
        'patients': patients,
    })


@login_required
@user_passes_test(is_doctor, login_url='login')
def doctor_consultations(request):
    consultations = ConsultationHistory.objects.all().order_by('-created_at')
    return render(request, 'core/doctor/doctor_consultations.html', {
        'consultations': consultations,
    })
