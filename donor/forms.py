from django import forms
from .models import FoodListing, FoodRequest, DonorReport

class FoodListingForm(forms.ModelForm):
    class Meta:
        model = FoodListing
        fields = ['food_name', 'food_type', 'quantity', 'prepared_time', 'expiry_time', 'notes']
        widgets = {
            'prepared_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class FoodRequestForm(forms.ModelForm):
    needs_delivery = forms.BooleanField(
        required=False,
        initial=False,
        label="Request Volunteer Logistics (Driver) Transport Support",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = FoodRequest
        fields = ['pickup_time', 'contact_person', 'contact_number', 'vehicle_info']
        widgets = {
            'pickup_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class DonorReportForm(forms.ModelForm):
    class Meta:
        model = DonorReport
        fields = ['report_text']
        widgets = {
            'report_text': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Please describe the issue with the receiver (e.g., inappropriate behavior, failure to pick up food, etc.)...',
                'class': 'form-control'
            }),
        }
        labels = {
            'report_text': 'Report Details',
        }
