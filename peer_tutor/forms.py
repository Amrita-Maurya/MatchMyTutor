from django import forms
from django.contrib.auth.models import User
from .models import Availability, Review


class SignupForm(forms.Form):
    ROLE_CHOICES = [
        ('student', 'Student — I want to find tutors'),
        ('tutor', 'Tutor — I want to offer tutoring'),
        ('both', 'Both — I want to do both'),
    ]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name', 'autocomplete': 'name'}),
        label='Full Name',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'Minimum 8 characters'}),
        label='Password',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat your password'}),
        label='Confirm Password',
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label='I am signing up as',
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Your password'}),
    )


class SubjectForm(forms.Form):
    subject_name = forms.CharField(
        max_length=100,
        label='Subject',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Mathematics, Python, Physics',
            'autocomplete': 'off',
        }),
    )

    def clean_subject_name(self):
        name = self.cleaned_data['subject_name'].strip()
        if not name:
            raise forms.ValidationError('Subject name cannot be empty.')
        return name.title()


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'date': 'Date',
            'start_time': 'Start Time',
            'end_time': 'End Time',
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-radio'}),
        label='Rating',
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience with this tutor...',
            }),
        }
        labels = {
            'comment': 'Your Review (optional)',
        }
