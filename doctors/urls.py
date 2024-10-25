from django.urls import path
from .views import DoctorLandingPageView, CalendarListView

urlpatterns = [
    path('dashboard/', DoctorLandingPageView.as_view(), name='doctor-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
]
