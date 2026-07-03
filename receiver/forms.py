from django import forms
from .models import Feedback, Report

class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-rating'}),
        label="Rate your experience"
    )

    class Meta:
        model = Feedback
        fields = ['rating', 'feedback_text']
        widgets = {
            'feedback_text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your feedback about the food quality, packaging, timeliness, or any other aspects of the donation...',
                'class': 'form-control'
            }),
        }
        labels = {
            'feedback_text': 'Additional Comments (Optional)',
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_text']
        widgets = {
            'report_text': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Please describe the issue with the food donation (e.g., quality, safety concerns, packaging issues, etc.)...',
                'class': 'form-control'
            }),
        }
        labels = {
            'report_text': 'Report Details',
        }
