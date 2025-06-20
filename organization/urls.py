from django.urls import path
from . import views

urlpatterns = [
    path('organization_list', views.OrganizationList.as_view()),
    path('<int:pk>', views.OrganizationDetails.as_view()),
    path('view_doctors/<int:id>', views.OrganizationViewDoctors.as_view()),
    path('no_of_doctors/<int:pk>', views.OrganizationNoOfDoctors.as_view())
]
