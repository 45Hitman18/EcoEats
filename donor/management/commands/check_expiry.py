from django.core.management.base import BaseCommand
from django.utils import timezone
from donor.models import FoodListing, FoodRequest
from accounts.models import ActivityLog

class Command(BaseCommand):
    help = 'Check for expired food listings and update their status'

    def handle(self, *args, **options):
        self.stdout.write('Checking for expired food listings...')

        expired_listings = FoodListing.objects.filter(
            expiry_time__lt=timezone.now(),
            status__in=['available', 'requested']
        ).exclude(is_deleted=True)

        updated_count = 0
        for listing in expired_listings:
            old_status = listing.status
            listing.status = 'expired'
            listing.save(update_fields=['status', 'updated_at'])

            # Log the expiry
            ActivityLog.objects.create(
                user=listing.donor,
                action='Food Listing Expired',
                description=f'Food listing "{listing.food_name}" expired automatically',
                action_type='food_expired'
            )

            # Disable any pending requests for this listing
            pending_requests = FoodRequest.objects.filter(
                food_listing=listing,
                status='pending'
            )
            for request in pending_requests:
                request.status = 'rejected'
                request.save(update_fields=['status'])

                # Log the request rejection
                ActivityLog.objects.create(
                    user=request.requester,
                    action='Request Auto-Rejected',
                    description=f'Request for "{listing.food_name}" was auto-rejected due to expiry',
                    action_type='request_rejected'
                )

            updated_count += 1
            self.stdout.write(
                f'  - {listing.food_name} by {listing.donor.username}: {old_status} -> expired'
            )

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} expired listings')
            )
        else:
            self.stdout.write('No expired listings found')

        self.stdout.write('Expiry check completed.')
