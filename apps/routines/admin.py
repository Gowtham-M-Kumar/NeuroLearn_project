from django.contrib import admin
from .models import Routine, Task, TaskCompletion, RoutineSchedule, TimetableEntry, ChildRoutine


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'is_active', 'created_at', 'task_count']
    list_filter = ['is_active', 'created_at', 'created_by__role']
    search_fields = ['title', 'description', 'created_by__email', 'child__username', 'child__first_name']
    autocomplete_fields = ['child']
    readonly_fields = ['created_at', 'updated_at']
    
    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'routine', 'order', 'estimated_duration', 'is_required']
    list_filter = ['is_required', 'routine__is_active', 'created_at']
    search_fields = ['title', 'description', 'routine__title']
    ordering = ['routine', 'order']
    readonly_fields = ['created_at']


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ['task', 'child', 'completed_at', 'completed_by']
    list_filter = ['completed_at', 'task__routine__is_active']
    search_fields = ['task__title', 'child__email', 'notes']
    readonly_fields = ['completed_at']
    date_hierarchy = 'completed_at'


@admin.register(RoutineSchedule)
class RoutineScheduleAdmin(admin.ModelAdmin):
    list_display = ['routine', 'child', 'day_of_week', 'start_time', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'routine__is_active']
    search_fields = ['routine__title', 'child__email']
    ordering = ['day_of_week', 'start_time']


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['routine', 'day_type', 'time', 'task_type']
    list_filter = ['day_type', 'task_type']
    search_fields = ['routine__child__first_name', 'routine__child__last_name', 'custom_description']
    ordering = ['routine', 'day_type', 'time']
@admin.register(ChildRoutine)
class ChildRoutineAdmin(admin.ModelAdmin):
    list_display = ['title', 'child', 'time', 'repeat_days', 'notify_parent', 'is_active']
    list_filter = ['is_active', 'notify_parent', 'time']
    search_fields = ['title', 'child__email', 'child__first_name']
    ordering = ['time']
