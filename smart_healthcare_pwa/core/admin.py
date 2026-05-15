from django.contrib import admin
from .models import Symptom, Disease, Medication, ConsultationHistory, Appointment

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    filter_horizontal = ('symptoms',)

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'disease')
    list_filter = ('disease',)
    search_fields = ('name',)

@admin.register(ConsultationHistory)
class ConsultationHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'predicted_disease', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'predicted_disease')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('user__username', 'reason')
