from django.urls import path
from . import views
from . import doctor_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('symptoms/', views.symptom_checker, name='symptoms'),
    path('results/<int:history_id>/', views.results_view, name='results'),
    path('history/', views.history_view, name='history'),
    path('appointment/', views.book_appointment, name='book_appointment'),
    path('health-tips/', views.health_tips, name='health_tips'),
    path('disease/<str:disease_name>/', views.disease_detail, name='disease_detail'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('profile/', views.profile_view, name='profile'),

    # Doctor Portal
    path('doctor/', doctor_views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', doctor_views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointments/<int:appointment_id>/<str:new_status>/', doctor_views.doctor_update_appointment, name='doctor_update_appointment'),
    path('doctor/patients/', doctor_views.doctor_patients, name='doctor_patients'),
    path('doctor/consultations/', doctor_views.doctor_consultations, name='doctor_consultations'),
]
