# users/urls.py
from django.urls import path, include

from .views import (
    DeleteAccountView,
    SimpleUserRegistrationView,
    UserRegistrationView,
    LoginView,
    UserDetailView,
    StaffLandingPageView,
    CalendarListView,
    MeProfileUpdateView,
)

staff_patterns = [
    path('dashboard/', StaffLandingPageView.as_view(), name='staff-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
]

urlpatterns = [
    path("new-register/", SimpleUserRegistrationView.as_view(), name="new-register"),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/', UserDetailView.as_view(), name='user-detail'),

    # Unified profile endpoint (GET returns flattened profile; PATCH persists fields incl. chatgroup_nickname)
    path('profile/', MeProfileUpdateView.as_view(), name='users-profile'),

    path('staff/', include((staff_patterns, 'users'), namespace='staff')),

    path('patient/', include('patients.urls')),
    path('doctor/', include('doctors.urls')),

    path("account/delete/", DeleteAccountView.as_view(), name="account-delete"),
]
