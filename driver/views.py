from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from donor.models import FoodListing, FoodRequest, Notification
from accounts.models import Profile
from .forms import DriverOnboardingForm

@login_required
def dashboard(request):
    if request.user.profile.role != 'driver':
        messages.error(request, "Access restricted to volunteer drivers.")
        return redirect('accounts:home')

    # Force onboarding flow
    if not request.user.profile.is_driver_onboarded:
        return redirect('driver:onboarding')

    # Get active deliveries assigned to this driver
    active_deliveries = FoodRequest.objects.filter(
        driver=request.user, 
        status='approved',
        delivery_status__in=['accepted', 'picked_up']
    ).select_related('food_listing', 'food_listing__donor', 'requester')
    active_delivery = active_deliveries.first()

    # Get available delivery requests that need a driver (public pool)
    available_jobs = FoodRequest.objects.filter(
        status='approved',
        delivery_status='pending_driver',
        driver__isnull=True
    ).select_related('food_listing', 'food_listing__donor', 'requester')

    # Get direct delivery requests specifically assigned to this driver by donors
    direct_requests = FoodRequest.objects.filter(
        driver=request.user,
        status='approved',
        delivery_status='pending_driver'
    ).select_related('food_listing', 'food_listing__donor', 'requester')

    # Calculate driver statistics
    completed_deliveries = FoodRequest.objects.filter(
        driver=request.user,
        delivery_status='delivered'
    )
    completed_runs_count = completed_deliveries.count()
    
    total_weight_transported = completed_deliveries.aggregate(
        total=Sum('food_listing__quantity')
    )['total'] or 0

    co2_saved = round(total_weight_transported * 2.5, 1)

    context = {
        'active_delivery': active_delivery,
        'active_deliveries': active_deliveries,
        'available_jobs': available_jobs,
        'direct_requests': direct_requests,
        'completed_runs_count': completed_runs_count,
        'total_weight_transported': total_weight_transported,
        'co2_saved': co2_saved,
    }
    return render(request, 'driver/dashboard.html', context)

@login_required
def onboarding(request):
    if request.user.profile.role != 'driver':
        return redirect('accounts:home')

    if request.user.profile.is_driver_onboarded:
        return redirect('driver:dashboard')

    profile = request.user.profile
    if request.method == 'POST':
        form = DriverOnboardingForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            driver_profile = form.save(commit=False)
            driver_profile.is_driver_onboarded = True
            driver_profile.is_verified = True # Self-verify for testing convenience
            driver_profile.save()
            messages.success(request, "Registration and verification documentation submitted successfully! Welcome to the Logistics Dispatch Center.")
            return redirect('driver:dashboard')
    else:
        form = DriverOnboardingForm(instance=profile)

    return render(request, 'driver/onboarding.html', {'form': form})

@login_required
def claim_delivery(request, request_id):
    if request.user.profile.role != 'driver':
        return redirect('accounts:home')

    if not request.user.profile.is_driver_onboarded:
        return redirect('driver:onboarding')

    food_request = get_object_or_404(
        FoodRequest, 
        id=request_id, 
        status='approved', 
        delivery_status='pending_driver', 
        driver__isnull=True
    )
    
    food_request.driver = request.user
    food_request.delivery_status = 'accepted'
    food_request.save()

    # Notify donor and receiver
    Notification.objects.create(
        recipient=food_request.food_listing.donor,
        notification_type='request_approved',
        title='Driver Assigned to Delivery',
        message=f'Volunteer driver {request.user.username} has accepted the transport request for "{food_request.food_listing.food_name}" and is heading to pick it up.'
    )
    Notification.objects.create(
        recipient=food_request.requester,
        notification_type='request_approved',
        title='Driver Assigned to Delivery',
        message=f'Volunteer driver {request.user.username} has accepted the transport request for "{food_request.food_listing.food_name}" and will deliver it to you.'
    )

    messages.success(request, f'Delivery task for "{food_request.food_listing.food_name}" claimed successfully!')
    return redirect('driver:dashboard')

@login_required
def update_status(request, request_id):
    if request.user.profile.role != 'driver':
        return redirect('accounts:home')

    if not request.user.profile.is_driver_onboarded:
        return redirect('driver:onboarding')

    food_request = get_object_or_404(FoodRequest, id=request_id, driver=request.user)
    new_status = request.POST.get('status')

    if new_status == 'picked_up' and food_request.delivery_status == 'accepted':
        food_request.delivery_status = 'picked_up'
        food_request.save()
        
        # Notify receiver
        Notification.objects.create(
            recipient=food_request.requester,
            notification_type='request_approved',
            title='Food Picked Up by Driver',
            message=f'Volunteer driver {request.user.username} has picked up the food from the donor and is in transit to your shelter.'
        )
        messages.success(request, 'Delivery marked as Picked Up! Safe travels.')
        
    elif new_status == 'delivered' and food_request.delivery_status == 'picked_up':
        if 'delivery_photo' in request.FILES:
            food_request.delivery_photo = request.FILES['delivery_photo']
        
        food_request.delivery_status = 'delivered'
        food_request.status = 'completed'
        food_request.save()

        # Update associated listing status to donated
        listing = food_request.food_listing
        listing.status = 'donated'
        listing.save()

        # Notify donor and receiver
        Notification.objects.create(
            recipient=listing.donor,
            notification_type='request_completed',
            title='Donation Delivered',
            message=f'Volunteer driver {request.user.username} has successfully delivered your food listing "{listing.food_name}" to the receiver.'
        )
        Notification.objects.create(
            recipient=food_request.requester,
            notification_type='request_completed',
            title='Donation Delivered',
            message=f'Volunteer driver {request.user.username} has delivered "{listing.food_name}" to your center. Please rate your experience!'
        )
        messages.success(request, 'Congratulations! Delivery completed successfully. Thank you for your service!')

    return redirect('driver:dashboard')

@login_required
def accept_direct_request(request, request_id):
    if request.user.profile.role != 'driver':
        return redirect('accounts:home')

    food_req = get_object_or_404(
        FoodRequest, 
        id=request_id, 
        driver=request.user, 
        status='approved', 
        delivery_status='pending_driver'
    )

    food_req.delivery_status = 'accepted'
    food_req.save()

    # Notify donor & NGO
    Notification.objects.create(
        recipient=food_req.food_listing.donor,
        notification_type='request_approved',
        title='Direct Transport Request Accepted',
        message=f'Volunteer driver {request.user.username} has accepted your direct request for "{food_req.food_listing.food_name}" and is proceeding to pickup.'
    )
    Notification.objects.create(
        recipient=food_req.requester,
        notification_type='request_approved',
        title='Driver Dispatched for Delivery',
        message=f'Volunteer driver {request.user.username} is heading to pick up and deliver your claimed food listing "{food_req.food_listing.food_name}".'
    )

    messages.success(request, f'Direct delivery request for "{food_req.food_listing.food_name}" accepted successfully!')
    return redirect('driver:dashboard')

@login_required
def decline_direct_request(request, request_id):
    if request.user.profile.role != 'driver':
        return redirect('accounts:home')

    food_req = get_object_or_404(
        FoodRequest, 
        id=request_id, 
        driver=request.user, 
        status='approved', 
        delivery_status='pending_driver'
    )

    # Reset driver fields so it returns to public pool
    donor = food_req.food_listing.donor
    food_req.driver = None
    food_req.delivery_status = 'pending_driver' # Keep pending driver for other drivers
    food_req.save()

    # Notify donor
    Notification.objects.create(
        recipient=donor,
        notification_type='request_rejected',
        title='Direct Transport Request Declined',
        message=f'Volunteer driver {request.user.username} has declined your direct transport request. The shipment is now listed in the public dispatch pool.'
    )

    messages.warning(request, f'Direct request declined. Shipment has been sent back to the public pool.')
    return redirect('driver:dashboard')


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def update_location(request):
    if request.user.profile.role != 'driver':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            if lat is not None and lng is not None:
                profile = request.user.profile
                profile.latitude = lat
                profile.longitude = lng
                profile.save(update_fields=['latitude', 'longitude'])
                return JsonResponse({'success': True})
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

