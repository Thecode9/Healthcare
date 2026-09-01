from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Symptom,
    Disease,
    Medication,
    ConsultationHistory,
    Appointment,
    UserProfile,
    Precaution,
)


class ModelTestCase(TestCase):
    """Test cases for Django data models."""

    def setUp(self):
        self.symptom = Symptom.objects.create(name="headache")
        self.disease = Disease.objects.create(name="Migraine", description="Severe headache disorder")
        self.disease.symptoms.add(self.symptom)

        self.user = User.objects.create_user(username="testpatient", password="Password123!")

    def test_symptom_properties(self):
        self.assertEqual(self.symptom.key, "headache")
        self.assertEqual(self.symptom.label, "Headache")
        self.assertEqual(str(self.symptom), "Headache")

    def test_disease_str(self):
        self.assertEqual(str(self.disease), "Migraine")

    def test_consultation_history_str(self):
        consult = ConsultationHistory.objects.create(
            user=self.user,
            predicted_disease="Migraine",
            confidence_score=95.5,
            symptoms_reported="headache"
        )
        self.assertIn("testpatient", str(consult))
        self.assertIn("Migraine", str(consult))

    def test_appointment_str(self):
        future_date = timezone.now() + timedelta(days=2)
        appt = Appointment.objects.create(
            user=self.user,
            appointment_date=future_date,
            reason="Checkup",
            status="PENDING"
        )
        self.assertIn("testpatient", str(appt))
        self.assertIn("PENDING", str(appt))


class PatientViewsTestCase(TestCase):
    """Test cases for patient web application views and authentication routing."""

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="patient1", password="Password123!")
        self.symptom = Symptom.objects.create(name="fever")

    def test_home_redirects_unauthenticated(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("login"))

    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "username": "patient1",
            "password": "Password123!"
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_authenticated(self):
        self.client.login(username="patient1", password="Password123!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")

    def test_book_appointment_past_date_validation(self):
        self.client.login(username="patient1", password="Password123!")
        past_date_str = (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("book_appointment"), {
            "date": past_date_str,
            "reason": "Routine Checkup"
        })
        self.assertRedirects(response, reverse("book_appointment"))
        self.assertEqual(Appointment.objects.count(), 0)

    def test_book_appointment_success(self):
        self.client.login(username="patient1", password="Password123!")
        future_date_str = (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("book_appointment"), {
            "date": future_date_str,
            "reason": "Routine Checkup"
        })
        self.assertRedirects(response, reverse("history"))
        self.assertEqual(Appointment.objects.count(), 1)


class DoctorPortalAccessTestCase(TestCase):
    """Test cases for Doctor Clinical Portal security and access controls."""

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="regularpatient", password="Password123!")
        self.doctor = User.objects.create_user(username="drsmith", password="Password123!", is_staff=True)

    def test_unauthenticated_denied_doctor_dashboard(self):
        response = self.client.get(reverse("doctor_dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('doctor_dashboard')}")


    def test_regular_patient_redirected_from_doctor_dashboard(self):
        self.client.login(username="regularpatient", password="Password123!")
        response = self.client.get(reverse("doctor_dashboard"))
        # Logged-in non-staff user gets redirected via doctor_login back to patient dashboard
        self.assertRedirects(response, f"{reverse('doctor_login')}?next={reverse('doctor_dashboard')}", fetch_redirect_response=False)

    def test_doctor_access_doctor_dashboard(self):
        self.client.login(username="drsmith", password="Password123!")
        response = self.client.get(reverse("doctor_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/doctor/doctor_dashboard.html")

    def test_doctor_update_appointment_status(self):
        self.client.login(username="drsmith", password="Password123!")
        appt = Appointment.objects.create(
            user=self.patient,
            appointment_date=timezone.now() + timedelta(days=1),
            reason="Medical consultation",
            status="PENDING"
        )
        url = reverse("doctor_update_appointment", kwargs={"appointment_id": appt.id, "new_status": "CONFIRMED"})
        response = self.client.get(url)
        self.assertRedirects(response, reverse("doctor_appointments"))
        appt.refresh_from_db()
        self.assertEqual(appt.status, "CONFIRMED")


