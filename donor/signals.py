from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FoodRequest, Notification

@receiver(post_save, sender=FoodRequest)
def create_request_notification(sender, instance, created, **kwargs):
    """
    Automatically create a notification for the donor when a receiver makes a food request.
    """
    if created:
        # Get the donor from the food listing
        donor = instance.food_listing.donor
        
        # Create notification for the donor
        Notification.objects.create(
            recipient=donor,
            notification_type='new_request',
            title=f'New Request for {instance.food_listing.food_name}',
            message=f'{instance.requester.get_full_name() or instance.requester.username} has requested "{instance.food_listing.food_name}". Quantity: {instance.food_listing.quantity}',
            related_request=instance
        )

@receiver(post_save, sender=FoodRequest)
def create_status_update_notification(sender, instance, created, **kwargs):
    """
    Create notification for receiver when request status changes.
    """
    if not created:  # Only for updates, not new requests
        requester = instance.requester
        
        if instance.status == 'approved':
            Notification.objects.create(
                recipient=requester,
                notification_type='request_approved',
                title='Request Approved!',
                message=f'Your request for "{instance.food_listing.food_name}" has been approved by the donor.',
                related_request=instance
            )
        elif instance.status == 'rejected':
            Notification.objects.create(
                recipient=requester,
                notification_type='request_rejected',
                title='Request Rejected',
                message=f'Your request for "{instance.food_listing.food_name}" has been rejected.',
                related_request=instance
            )
        elif instance.status == 'completed':
            Notification.objects.create(
                recipient=requester,
                notification_type='request_completed',
                title='Request Completed!',
                message=f'Your request for "{instance.food_listing.food_name}" has been marked as completed.',
                related_request=instance
            )
