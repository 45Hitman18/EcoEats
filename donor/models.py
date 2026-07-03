from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class FoodListing(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=200)
    FOOD_TYPE_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non-veg', 'Non-Vegetarian'),
    ]
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    prepared_time = models.DateTimeField(default=timezone.now)
    expiry_time = models.DateTimeField(default=timezone.now() + timedelta(hours=24))
    pickup_location = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('requested', 'Requested'),
        ('donated', 'Donated'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    is_deleted = models.BooleanField(default=False)  # Soft delete field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.food_name} by {self.donor.username}'

    @property
    def is_expired(self):
        return timezone.now() > self.expiry_time

    def check_and_update_expiry(self):
        """Check if food has expired and update status accordingly"""
        if self.is_expired and self.status != 'expired':
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    class Meta:
        ordering = ['-created_at']

class FoodRequest(models.Model):
    food_listing = models.ForeignKey(FoodListing, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    pickup_time = models.DateTimeField(default=timezone.now)
    contact_person = models.CharField(max_length=100, default='')
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    vehicle_info = models.CharField(max_length=200, blank=True, null=True)
    
    # Volunteer logistics fields
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_deliveries')
    delivery_status = models.CharField(
        max_length=20, 
        choices=[
            ('none', 'No Delivery Needed'),
            ('pending_driver', 'Awaiting Driver'),
            ('accepted', 'Accepted by Driver'),
            ('picked_up', 'Picked Up'),
            ('delivered', 'Delivered')
        ], 
        default='none'
    )
    delivery_photo = models.ImageField(upload_to='delivery_proofs/', null=True, blank=True)

    def __str__(self):
        return f'Request for {self.food_listing.food_name} by {self.requester.username}'

class DonorReport(models.Model):
    food_request = models.OneToOneField(FoodRequest, on_delete=models.CASCADE, related_name='donor_report')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The donor reporting the issue")
    report_text = models.TextField(help_text="Details of the report")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report by {self.reporter.username} for {self.food_request.requester.username} on {self.food_request.food_listing.food_name}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    NOTIFICATION_TYPE_CHOICES = [
        ('new_request', 'New Food Request'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('request_completed', 'Request Completed'),
        ('food_expiring', 'Food Expiring Soon'),
    ]
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_request = models.ForeignKey(FoodRequest, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.notification_type} for {self.recipient.username}'
