from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, TeacherProfile, ChildProfile


class CustomUserCreationForm(forms.ModelForm):
    """Simplified form for creating new users with no constraints"""
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'register-input'}),
        required=True
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.UserRole.choices,
        widget=forms.Select(attrs={'class': 'register-input'}),
        required=True,
        initial=CustomUser.UserRole.CHILD,
        label='I am a'
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'register-input'}),
            'last_name': forms.TextInput(attrs={'class': 'register-input'}),
            'email': forms.TextInput(attrs={'class': 'register-input'}),  # Use TextInput instead of EmailInput to be less strict
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields except email and password optional
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['email'].required = True
    
    def clean_email(self):
        """Allow any email format and handle duplicates"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email is required')
        
        # If email already exists, append a timestamp to make it unique
        if CustomUser.objects.filter(email=email).exists():
            import time
            email = f"{email.split('@')[0]}_{int(time.time())}@{email.split('@')[1] if '@' in email else 'example.com'}"
        
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set the password without any validation
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user



class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form using email"""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'login-input'})
        self.fields['password'].widget.attrs.update({'class': 'login-input'})


class TeacherProfileForm(forms.ModelForm):
    """Form for teacher profile creation/editing"""
    
    class Meta:
        model = TeacherProfile
        fields = ('classroom_info', 'grade_level')
        widgets = {
            'classroom_info': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ChildProfileForm(forms.ModelForm):
    """Form for child profile creation/editing"""
    
    class Meta:
        model = ChildProfile
        fields = ('age', 'diagnosis_info', 'learning_level')
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'diagnosis_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'learning_level': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('beginner', 'Beginner'),
                ('intermediate', 'Intermediate'),
                ('advanced', 'Advanced'),
            ]),
        }


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
 