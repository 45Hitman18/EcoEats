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
    ambient_temperature = models.FloatField(default=25.0)
    packaging_type = models.CharField(max_length=20, default='boxed')
    ml_category = models.CharField(max_length=20, default='veg')

    def __str__(self):
        return f'{self.food_name} by {self.donor.username}'

    def calculate_quality_score(self):
        """Calculates an AI-based food quality score between 0 and 100."""
        score = 65.0
        
        # Packaging
        pack_scores = {
            'refrigerated': 20.0,
            'airtight': 15.0,
            'boxed': 10.0,
            'open': 0.0
        }
        score += pack_scores.get(self.packaging_type, 10.0)
        
        # Category base
        cat_scores = {
            'bakery': 15.0,
            'veg': 10.0,
            'cooked': 5.0,
            'dairy': 5.0,
            'non-veg': 0.0
        }
        score += cat_scores.get(self.ml_category, 10.0)
        
        # Temperature Penalty
        temp_penalty = max(0.0, (self.ambient_temperature - 20.0) * 1.5)
        score -= temp_penalty
        
        # Time since prep and predicted shelf-life decay
        from django.utils import timezone
        now = timezone.now()
        hours_since_prep = max(0.0, (now - self.prepared_time).total_seconds() / 3600.0)
        
        # Query loaded Random Forest model dynamically
        from donor.apps import DonorConfig
        model = DonorConfig.model
        feature_columns = DonorConfig.feature_columns
        
        predicted_shelf_life = 24.0  # default baseline
        if model and feature_columns:
            try:
                input_dict = {col: 0.0 for col in feature_columns}
                input_dict['prep_age_hours'] = hours_since_prep
                input_dict['temperature'] = self.ambient_temperature
                
                cat_col = f"category_{self.ml_category}"
                if cat_col in input_dict:
                    input_dict[cat_col] = 1.0
                    
                pack_col = f"packaging_{self.packaging_type}"
                if pack_col in input_dict:
                    input_dict[pack_col] = 1.0
                    
                input_vector = [input_dict[col] for col in feature_columns]
                predicted_shelf_life = float(model.predict([input_vector])[0])
            except Exception:
                pass
                
        total_span = max(1.0, hours_since_prep + predicted_shelf_life)
        remaining_ratio = max(0.0, 1.0 - (hours_since_prep / total_span))
        
        # Delivery duration penalty
        active_request = self.requests.filter(status='completed').first() or self.requests.filter(delivery_status='picked_up').first()
        delivery_duration_hours = 0.0
        if active_request:
            if active_request.transit_start_time:
                end_time = active_request.transit_end_time or now
                delivery_duration_hours = max(0.0, (end_time - active_request.transit_start_time).total_seconds() / 3600.0)
                
        score -= (delivery_duration_hours * 5.0)
        
        # Freshness multiplier
        score = score * remaining_ratio
        
        return int(max(0, min(100, score)))

    @property
    def quality_score(self):
        return self.calculate_quality_score()

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
    transit_start_time = models.DateTimeField(null=True, blank=True)
    transit_end_time = models.DateTimeField(null=True, blank=True)

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
    priority_score = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-priority_score', '-created_at']
    
    def __str__(self):
        return f'{self.notification_type} for {self.recipient.username} (Score: {self.priority_score})'

    def calculate_priority(self):
        """Calculates a smart priority score based on expiry, distance, availability, food category, and urgency."""
        score = 0.0
        
        # 1. Base Urgency weight based on notification type
        urgency_weights = {
            'food_expiring': 100.0,
            'new_request': 80.0,
            'request_approved': 60.0,
            'request_completed': 40.0,
            'request_rejected': 30.0,
        }
        score += urgency_weights.get(self.notification_type, 10.0)
        
        req = self.related_request
        if req:
            listing = req.food_listing
            
            # 2. Food Expiry factor
            if listing and listing.expiry_time:
                from django.utils import timezone
                now = timezone.now()
                if listing.expiry_time > now:
                    time_to_expiry = listing.expiry_time - now
                    hours_left = time_to_expiry.total_seconds() / 3600.0
                    
                    if hours_left <= 3:
                        score += 150.0  # Critical
                    elif hours_left <= 6:
                        score += 90.0   # High urgency
                    elif hours_left <= 12:
                        score += 50.0
                    elif hours_left <= 24:
                        score += 20.0
                else:
                    score -= 100.0  # Expired
                    
            # 3. Food Category factor
            if listing and listing.food_type:
                if listing.food_type == 'non-veg':
                    score += 40.0  # High decay risk
                elif listing.food_type == 'veg':
                    score += 20.0

            # 4. Distance factor (Haversine formula between donor and recipient/NGO)
            donor = listing.donor if listing else None
            recipient = req.requester
            if donor and recipient and hasattr(donor, 'profile') and hasattr(recipient, 'profile'):
                d_prof = donor.profile
                r_prof = recipient.profile
                if d_prof.latitude is not None and d_prof.longitude is not None and r_prof.latitude is not None and r_prof.longitude is not None:
                    import math
                    lat1, lon1 = float(d_prof.latitude), float(d_prof.longitude)
                    lat2, lon2 = float(r_prof.latitude), float(r_prof.longitude)
                    
                    rad = math.pi / 180.0
                    dlat = (lat2 - lat1) * rad
                    dlon = (lon2 - lon1) * rad
                    a = math.sin(dlat/2)**2 + math.cos(lat1*rad) * math.cos(lat2*rad) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance_km = 6371.0 * c
                    
                    if distance_km <= 5.0:
                        score += 50.0
                    elif distance_km <= 15.0:
                        score += 30.0
                    else:
                        score += 10.0
                        
            # 5. NGO availability / Driver availability
            if recipient and hasattr(recipient, 'profile'):
                if recipient.profile.is_verified:
                    score += 20.0
                    
            if donor and hasattr(donor, 'profile') and donor.profile.latitude is not None:
                from accounts.models import Profile
                lat = float(donor.profile.latitude)
                lon = float(donor.profile.longitude)
                lat_delta = 0.09  # approx 10km
                lon_delta = 0.11
                drivers_count = Profile.objects.filter(
                    role='driver',
                    is_driver_onboarded=True,
                    is_verified=True,
                    latitude__range=(lat - lat_delta, lat + lat_delta),
                    longitude__range=(lon - lon_delta, lon + lon_delta)
                ).count()
                
                if drivers_count > 0:
                    score += min(30.0, drivers_count * 10.0)
                    
        return score

    def save(self, *args, **kwargs):
        try:
            self.priority_score = self.calculate_priority()
        except Exception:
            self.priority_score = 0.0
        super().save(*args, **kwargs)
