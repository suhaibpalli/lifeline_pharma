from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, PatientProfile, PharmacyProfile, Address, EmailVerification

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'date_joined']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Account info', {'fields': ('user_type', 'is_verified', 'verification_token')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'gender', 'emergency_contact_name', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PharmacyProfile)
class PharmacyProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'license_number', 'city', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'city', 'state', 'created_at']
    search_fields = ['business_name', 'license_number', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_pharmacies', 'reject_pharmacies']
    
    def approve_pharmacies(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} pharmacies have been approved.')
    approve_pharmacies.short_description = "Approve selected pharmacies"
    
    def reject_pharmacies(self, request, queryset):
        queryset.update(is_approved=False, approved_by=None, approved_at=None)
        self.message_user(request, f'{queryset.count()} pharmacies have been rejected.')
    reject_pharmacies.short_description = "Reject selected pharmacies"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'address_type', 'city', 'state', 'is_default']
    list_filter = ['address_type', 'state', 'is_default']
    search_fields = ['user__email', 'name', 'city']

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']

admin.site.register(CustomUser, CustomUserAdmin)
