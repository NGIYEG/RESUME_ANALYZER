from django import forms
from Applicantapp.models import Applicant
from Companyapp.models import JobAdvertised


from django import forms
from django.contrib.auth.models import User
from .models import Applicant
from Companyapp.models import JobAdvertised


class ApplicantApplyForm(forms.ModelForm):
    job = forms.ModelChoiceField(
        queryset=JobAdvertised.objects.all(),
        widget=forms.Select(attrs={
            "class": "w-full border-gray-300 rounded-lg px-3 py-2"
        }),
        label="Select Job"
    )

    class Meta:
        model = Applicant
        fields = [
            'first_name', 'last_name', 'email',
            'linkedIn_profile', 'portfolio_link',
            'resume', 'other_documents'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'last_name': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'email': forms.EmailInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'linkedIn_profile': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'portfolio_link': forms.URLInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'resume': forms.FileInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'other_documents': forms.FileInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
        }



class UserRegisterForm(forms.ModelForm):
    """Handles the Account Creation (Username/Password)"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "w-full border-gray-300 rounded-lg px-3 py-2",
        "placeholder": "Password"
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "w-full border-gray-300 rounded-lg px-3 py-2",
        "placeholder": "Confirm Password"
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

        help_texts = {
            'username': None,  
        }
        
        widgets = {
            'username': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'email': forms.EmailInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'first_name': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'last_name': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class ApplicantProfileForm(forms.ModelForm):
    """Handles the Resume & Details Upload during Sign Up"""
    class Meta:
        model = Applicant
        fields = ['phone', 'location', 'linkedIn_profile', 'portfolio_link', 'resume']
        widgets = {
            'phone': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2", "placeholder": "e.g., +254..."}),
            'location': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2", "placeholder": "City, Country"}),
            'linkedIn_profile': forms.TextInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'portfolio_link': forms.URLInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
            'resume': forms.FileInput(attrs={"class": "w-full border-gray-300 rounded-lg px-3 py-2"}),
        }