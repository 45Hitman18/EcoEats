from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from donor.models import FoodListing, FoodRequest
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populate database with sample food donations and mark them as completed'

    def handle(self, *args, **options):
        # Create sample donor user if not exists
        donor, created = User.objects.get_or_create(
            username='sample_donor',
            defaults={
                'email': 'donor@example.com',
                'first_name': 'Sample',
                'last_name': 'Donor'
            }
        )
        if created:
            donor.set_password('password123')
            donor.save()
            self.stdout.write(self.style.SUCCESS('Created sample donor user'))

        # Create sample receiver user if not exists
        receiver, created = User.objects.get_or_create(
            username='sample_receiver',
            defaults={
                'email': 'receiver@example.com',
                'first_name': 'Sample',
                'last_name': 'Receiver'
            }
        )
        if created:
            receiver.set_password('password123')
            receiver.save()
            self.stdout.write(self.style.SUCCESS('Created sample receiver user'))

        # Sample food data
        food_items = [
            {'name': 'Pizza Margherita', 'type': 'veg', 'quantity': 2},
            {'name': 'Chicken Biryani', 'type': 'non-veg', 'quantity': 3},
            {'name': 'Vegetable Curry', 'type': 'veg', 'quantity': 4},
            {'name': 'Fish Tacos', 'type': 'non-veg', 'quantity': 1},
        ]

        locations = [
            'Downtown Restaurant',
            'Community Center',
            'Hotel Kitchen',
            'School Cafeteria'
        ]

        for i, food in enumerate(food_items):
            # Create food listing
            listing = FoodListing.objects.create(
                donor=donor,
                food_name=food['name'],
                food_type=food['type'],
                quantity=food['quantity'],
                prepared_time=timezone.now() - timedelta(hours=random.randint(1, 24)),
                expiry_time=timezone.now() + timedelta(hours=random.randint(12, 48)),
                pickup_location=random.choice(locations),
                latitude=random.uniform(12.0, 13.0),
                longitude=random.uniform(77.0, 78.0),
                notes=f'Sample food item {i+1}',
                status='available'
            )

            # Create food request and mark as completed
            request = FoodRequest.objects.create(
                food_listing=listing,
                requester=receiver,
                status='completed',
                message='Sample request for testing',
                pickup_time=timezone.now() + timedelta(hours=random.randint(1, 6)),
                contact_person='Sample Receiver',
                contact_number='1234567890'
            )

            # Update listing status to donated
            listing.status = 'donated'
            listing.save()

            self.stdout.write(self.style.SUCCESS(f'Created food donation: {food["name"]} - Status: Completed'))

        self.stdout.write(self.style.SUCCESS('Successfully populated database with 4 sample food donations'))
