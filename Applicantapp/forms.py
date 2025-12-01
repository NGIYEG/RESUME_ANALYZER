from django import forms
from Applicantapp.models import Applicant
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
