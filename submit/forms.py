from django import forms
from .models import CodeSubmission


class CodeSubmissionForm(forms.ModelForm):
    class Meta:
        model = CodeSubmission
        fields = ['language', 'code', 'input_data']
        widgets = {
            'language': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'placeholder': 'Enter your code here...'}),
            'input_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter input data (optional)...'}),
        } 