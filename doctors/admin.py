# doctors/admin.py
from django.contrib import admin
from .models import Doctor, DoctorRequest, DoctorRating

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rates')
    search_fields = ('user__username', 'user__email')

@admin.register(DoctorRequest)
class DoctorRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('patient__username', 'doctor__username')

@admin.register(DoctorRating)
class DoctorRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'patient', 'stars', 'created_at')
    list_filter = ('stars',)
    search_fields = ('doctor__user__username', 'patient__username')
    
