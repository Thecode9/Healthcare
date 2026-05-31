from django.db import models
from django.contrib.auth.models import User

class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    symptoms = models.ManyToManyField(Symptom, related_name='diseases')

    def __str__(self):
        return self.name

class Medication(models.Model):
    name = models.CharField(max_length=100)
    dosage_instructions = models.TextField(blank=True, null=True)
    disease = models.ForeignKey(Disease, null=True, on_delete=models.SET_NULL, related_name='medications')
    
    def __str__(self):
        return f"{self.name} for {self.disease.name}"

class ConsultationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    predicted_disease = models.CharField(max_length=100)
    recommended_medication = models.TextField(blank=True, null=True)
    symptoms_reported = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.predicted_disease} on {self.created_at.strftime('%Y-%m-%d')}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')} [{self.status}]"

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    actively_on_medication = models.BooleanField(default=False)
    current_medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name}'s Profile"
