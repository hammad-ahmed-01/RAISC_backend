from django.urls import path
from .views import PatientLandingPageView, CalendarListView

urlpatterns = [
    path('dashboard/', PatientLandingPageView.as_view(), name='patient-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
]
