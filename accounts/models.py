from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('receiver', 'Receiver'),
        ('driver', 'Volunteer Logistics Driver'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='donor')
    location = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    license_document = models.FileField(upload_to='licenses/', null=True, blank=True, help_text='Upload government verified license (PDF only)')
    
    # Driver Onboarding fields
    vehicle_name = models.CharField(max_length=100, blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    aadhaar_card = models.CharField(max_length=12, blank=True, null=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    is_driver_onboarded = models.BooleanField(default=False)
    
    # Storage and capability settings for NGOs/Receivers
    bio = models.TextField(blank=True, null=True, help_text="Description of the organization's mission")
    has_fridge = models.BooleanField(default=False, help_text="Has cold storage capability")
    has_freezer = models.BooleanField(default=False, help_text="Has freezer storage capability")
    has_warmers = models.BooleanField(default=False, help_text="Has hot holding capability")
    vehicle_capacity = models.IntegerField(default=0, help_text="Maximum servings capacity for vehicle transport")
    max_capacity = models.IntegerField(default=100, help_text="Maximum distribution capacity (servings)")

    def __str__(self):
        return f'{self.user.username} - {self.role}'

    def get_badges(self):
        from django.db.models import Sum
        from donor.models import FoodListing, FoodRequest
        
        badges = []
        if self.role == 'donor':
            total_donated = FoodListing.objects.filter(donor=self.user, status='donated').aggregate(total=Sum('quantity'))['total'] or 0
            if total_donated >= 500:
                badges.append({'name': 'Zero-Waste Champion', 'color': 'bg-emerald text-white', 'icon': 'fa-crown'})
            if total_donated >= 250:
                badges.append({'name': 'Eco Pioneer', 'color': 'bg-success text-white', 'icon': 'fa-seedling'})
            if total_donated >= 100:
                badges.append({'name': '100 Meals Saved', 'color': 'bg-primary text-white', 'icon': 'fa-heart'})
            if total_donated >= 10:
                badges.append({'name': 'Food Rescuer', 'color': 'bg-info text-white', 'icon': 'fa-shield-halved'})
        elif self.role == 'receiver':
            total_claimed = FoodRequest.objects.filter(requester=self.user, status='completed').aggregate(total=Sum('food_listing__quantity'))['total'] or 0
            if total_claimed >= 500:
                badges.append({'name': 'Community Hero', 'color': 'bg-indigo text-white', 'icon': 'fa-shield-heart'})
            if total_claimed >= 250:
                badges.append({'name': 'Hunger Fighter', 'color': 'bg-primary text-white', 'icon': 'fa-utensils'})
            if total_claimed >= 100:
                badges.append({'name': '100 Meals Served', 'color': 'bg-success text-white', 'icon': 'fa-hands-helping'})
            if total_claimed >= 10:
                badges.append({'name': 'Active Distributor', 'color': 'bg-info text-white', 'icon': 'fa-truck-loading'})
        return badges

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('register', 'User Registration'),
        ('food_added', 'Food Listing Added'),
        ('food_updated', 'Food Listing Updated'),
        ('food_deleted', 'Food Listing Deleted'),
        ('request_made', 'Food Request Made'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('request_completed', 'Request Completed'),
        ('profile_updated', 'Profile Updated'),
    ]

    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, default='login')

    def __str__(self):
        return f'{self.action} - {self.user.username if self.user else "System"} - {self.created_at}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
