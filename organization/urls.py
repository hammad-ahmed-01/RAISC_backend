from django.urls import path
from . import views

urlpatterns = [
    path('organization_list', views.OrganizationList.as_view()),
    path('organization_details', views.OrganizationDetails.as_view()),
    path('view_doctors/', views.OrganizationViewDoctors.as_view()),
    path('no_of_doctors/', views.OrganizationNoOfDoctors.as_view()),
    path('view_doctor_calendar/', views.OrganizationDoctorViewCalendar.as_view()),
    path('register_doctor/', views.OrganizationRegisterDoctor.as_view())
]