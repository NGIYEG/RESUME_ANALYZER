from django import forms
from .models import Post, Department, JobAdvertised

class JobAdvertisedForm(forms.ModelForm):
    class Meta:
        model = JobAdvertised
        fields = ['department', 'post', 'deadline', 'keywords', 'max_applicants']

        widgets = {
            'department': forms.Select(attrs={
                'class': 'w-full border-gray-400 rounded-lg px-3 py-2'
            }),

            'post': forms.Select(attrs={
                'class': 'w-full border-gray-400 rounded-lg px-3 py-2'
            }),

            'deadline': forms.DateInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full border-gray-400 rounded-lg px-3 py-2'
            }),

            'keywords': forms.Textarea(attrs={
                'class': 'w-full border-gray-400 rounded-lg px-3 py-2',
                'rows': 4
            }),

            'max_applicants': forms.NumberInput(attrs={
                'class': 'w-full border-gray-400 rounded-lg px-3 py-2'
            }),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['department', 'title']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'w-full border-[#cb8700] rounded-lg shadow-sm px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full border-[#cb8700] rounded-lg shadow-sm px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
        }
        
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border-gray-300 rounded-lg shadow-sm px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            })
        }