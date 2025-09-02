from django.urls import path, include
from .views import (
    SimpleUserRegistrationView,
    UserRegistrationView,
    LoginView,
    UserDetailView,
    StaffLandingPageView,
    CalendarListView,
    MeProfileUpdateView,          # NEW
)

# Staff-only (unchanged)
staff_patterns = [
    path('dashboard/', StaffLandingPageView.as_view(), name='staff-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
]

urlpatterns = [
    path("new-register/" , SimpleUserRegistrationView.as_view(), name="new-register"),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/', UserDetailView.as_view(), name='user-detail'),

    # unified profile patch for any role
    path('profile/', MeProfileUpdateView.as_view(), name='users-profile'),

    # staff
    path('staff/', include((staff_patterns, 'users'), namespace='staff')),

    # role sub-routers
    path('patient/', include('patients.urls')),
    path('doctor/', include('doctors.urls')),
]
