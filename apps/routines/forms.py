from datetime import time
from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Routine,
    Task,
    TaskCompletion,
    RoutineSchedule,
    TimetableEntry
)

User = get_user_model()


# =========================
# ROUTINE FORM
# =========================
class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter routine title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the routine'
            })
        }


# =========================
# TASK FORM
# =========================
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'image',
            'estimated_duration',
            'is_required'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe the task'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 240,
                'placeholder': 'Duration (minutes)'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


# =========================
# TASK COMPLETION
# =========================
class TaskCompletionForm(forms.ModelForm):
    class Meta:
        model = TaskCompletion
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional notes'
            })
        }


# =========================
# ROUTINE SCHEDULE FORM
# =========================
class RoutineScheduleForm(forms.ModelForm):
    class Meta:
        model = RoutineSchedule
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            })
        }


# =========================
# TASK REORDER
# =========================
class TaskReorderForm(forms.Form):
    task_id = forms.IntegerField()
    new_order = forms.IntegerField()


# =========================
# TIMETABLE ENTRY FORM (FIXED)
# =========================
class TimetableEntryForm(forms.ModelForm):
    """
    12-hour time selection form that safely builds TimeField
    """

    HOUR_CHOICES = [(i, f"{i}") for i in range(1, 13)]
    MINUTE_CHOICES = [(i, f"{i:02d}") for i in range(0, 60, 5)]
    AM_PM_CHOICES = [('AM', 'AM'), ('PM', 'PM')]

    hour = forms.ChoiceField(
        choices=HOUR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    minute = forms.ChoiceField(
        choices=MINUTE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    am_pm = forms.ChoiceField(
        choices=AM_PM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TimetableEntry
        fields = [
            'day_type',
            'task_type',
            'custom_description',
            'notes'
        ]
        widgets = {
            'day_type': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(
                attrs={
                    'class': 'form-select',
                    'onchange': 'toggleCustomDescription(this)'
                }
            ),
            'custom_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Custom activity name'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional guidance'
            })
        }

    def clean(self):
        cleaned_data = super().clean()

        hour = cleaned_data.get('hour')
        minute = cleaned_data.get('minute')
        am_pm = cleaned_data.get('am_pm')

        if not (hour and minute and am_pm):
            raise forms.ValidationError("Please select a valid time.")

        hour = int(hour)
        minute = int(minute)

        # Convert to 24-hour format
        if am_pm == 'PM' and hour != 12:
            hour += 12
        if am_pm == 'AM' and hour == 12:
            hour = 0

        cleaned_data['time'] = time(hour, minute)

        # Validate custom activity
        if cleaned_data.get('task_type') == 'other' and not cleaned_data.get('custom_description'):
            self.add_error(
                'custom_description',
                'Please enter a custom activity name.'
            )

        return cleaned_data