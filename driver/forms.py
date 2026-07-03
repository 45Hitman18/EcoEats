from django import forms
from accounts.models import Profile

class DriverOnboardingForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['vehicle_name', 'vehicle_model', 'vehicle_number', 'aadhaar_card', 'license_document']
        widgets = {
            'vehicle_name': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'e.g. Maruti Suzuki Eeco, Honda Activa'
            }),
            'vehicle_model': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'e.g. 2022 XL Cargo'
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'e.g. DL-3C-AB-1234'
            }),
            'aadhaar_card': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': '12-digit Aadhaar Card Number',
                'maxlength': '12'
            }),
            'license_document': forms.FileInput(attrs={
                'class': 'form-control rounded-3',
                'accept': 'application/pdf'
            })
        }
        labels = {
            'vehicle_name': 'Vehicle Name',
            'vehicle_model': 'Vehicle Model / Year',
            'vehicle_number': 'Vehicle License Plate Number',
            'aadhaar_card': 'Aadhaar Card Number',
            'license_document': 'Driving License (PDF only)'
        }

    def clean_aadhaar_card(self):
        aadhaar = self.cleaned_data.get('aadhaar_card')
        if aadhaar:
            # Strip spaces or hyphens if any
            aadhaar = "".join(aadhaar.split())
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                raise forms.ValidationError("Aadhaar Card number must be exactly 12 numeric digits.")
        return aadhaar

    def clean_license_document(self):
        doc = self.cleaned_data.get('license_document')
        if doc:
            if not doc.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Driving License document must be in PDF format only.")
        else:
            raise forms.ValidationError("Please upload your Driving License PDF document for verification.")
        return doc
