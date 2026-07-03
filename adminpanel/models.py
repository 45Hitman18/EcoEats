from django.db import models

class ContactInquiry(models.Model):
    full_name = models.CharField(max_length=100)
    organization_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    organization_type = models.CharField(max_length=50, choices=[
        ('restaurant', 'Restaurant / Hotel'),
        ('manufacturer', 'Food Manufacturer'),
        ('distributor', 'Distributor / Warehouse'),
        ('nonprofit', 'Nonprofit / NGO'),
        ('other', 'Other'),
    ])
    donation_size = models.CharField(max_length=50, choices=[
        ('small', 'Small (occasional surplus)'),
        ('medium', 'Medium (regular donations)'),
        ('large', 'Large (bulk / palletized donations)'),
    ])
    location = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.organization_name}"
