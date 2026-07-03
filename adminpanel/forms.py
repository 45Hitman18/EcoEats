from django import forms
from donor.models import FoodListing
from django.contrib.auth.models import User

class FoodListingFilterForm(forms.Form):
    food_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search food name...'})
    )
    food_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + FoodListing.FOOD_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + FoodListing.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    donor = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(profile__role='donor'),
        empty_label="All Donors",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_quantity = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min quantity'})
    )
    max_quantity = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max quantity'})
    )
    expiry_from = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    expiry_to = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    pickup_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search location...'})
    )
