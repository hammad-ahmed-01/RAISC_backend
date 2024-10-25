from django.urls import path, include
from .views import UserRegistrationView, LoginView, UserDetailView, StaffLandingPageView, CalendarListView

# Define staff-specific URL patterns
staff_patterns = [
    path('dashboard/', StaffLandingPageView.as_view(), name='staff-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
]

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('staff/', include((staff_patterns, 'users'), namespace='staff')),
    path('patient/', include('patients.urls')),  # Include patient URLs
    path('doctor/', include('doctors.urls')),    # Include doctor URLs
]
