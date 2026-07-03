from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Feedback(models.Model):
    food_request = models.OneToOneField('donor.FoodRequest', on_delete=models.CASCADE, related_name='feedback')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the food quality and donation experience (1-5)"
    )
    feedback_text = models.TextField(blank=True, null=True, help_text="Optional feedback about the food and donation process")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.receiver.username} for {self.food_request.food_listing.food_name}"

class Report(models.Model):
    food_request = models.OneToOneField('donor.FoodRequest', on_delete=models.CASCADE, related_name='report')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The receiver reporting the issue")
    report_text = models.TextField(help_text="Details of the report")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report by {self.reporter.username} for {self.food_request.food_listing.food_name} by {self.food_request.food_listing.donor.username}"
