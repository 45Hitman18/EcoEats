from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message here...',
                'style': 'resize: none;'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control-file',
                'style': 'display: none;'
            })
        }
        labels = {
            'content': '',
            'file': ''
        }
