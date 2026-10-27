from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, TeacherProfile, ChildProfile, ParentProfile, ParentDevice


class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser"""
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'classroom_info', 'grade_level', 'assigned_children_count')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'classroom_info')
    filter_horizontal = ('assigned_children',)
    
    def assigned_children_count(self, obj):
        return obj.assigned_children.count()
    assigned_children_count.short_description = 'Assigned Children'


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'learning_level', 'primary_teacher')
    list_filter = ('learning_level', 'age')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('primary_teacher',)


# Register the custom user admin
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('assigned_children',)

@admin.register(ParentDevice)
class ParentDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'fcm_token', 'device_id', 'updated_at')
    search_fields = ('user__email', 'fcm_token')
