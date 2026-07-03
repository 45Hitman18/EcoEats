from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
import json
from donor.models import FoodListing, FoodRequest, Notification
from donor.forms import FoodRequestForm
from donor.utils import calculate_distance
from .models import Feedback, Report
from .forms import FeedbackForm

@login_required
def dashboard(request):
    if request.user.profile.role != 'receiver':
        return redirect('accounts:home')

    # Get user's requests with status badges
    user_requests = FoodRequest.objects.filter(requester=request.user).select_related('food_listing')
    completed_requests = user_requests.filter(status='completed')

    food_listings = FoodListing.objects.filter(status='available')

    # Apply filters
    food_type = request.GET.get('food_type')
    location = request.GET.get('location')
    expiry_filter = request.GET.get('expiry')
    radius_filter = request.GET.get('radius')  # Distance filter: 10, 20, 30 km

    if food_type:
        food_listings = food_listings.filter(food_type=food_type)
    if location:
        food_listings = food_listings.filter(pickup_location__icontains=location)
    if expiry_filter:
        from django.utils import timezone
        now = timezone.now()
        if expiry_filter == '1h':
            food_listings = food_listings.filter(expiry_time__lte=now + timezone.timedelta(hours=1))
        elif expiry_filter == '6h':
            food_listings = food_listings.filter(expiry_time__lte=now + timezone.timedelta(hours=6))
        elif expiry_filter == '24h':
            food_listings = food_listings.filter(expiry_time__lte=now + timezone.timedelta(hours=24))
    
    # Calculate distance and filter by radius
    user_profile = request.user.profile
    food_listings_with_distance = []
    
    if user_profile.latitude and user_profile.longitude:
        for food in food_listings:
            if food.latitude and food.longitude:
                distance = calculate_distance(
                    user_profile.latitude, user_profile.longitude,
                    food.latitude, food.longitude
                )
                food.distance = distance
                
                # Apply radius filter if specified
                if radius_filter:
                    try:
                        max_radius = float(radius_filter)
                        if distance <= max_radius:
                            food_listings_with_distance.append(food)
                    except ValueError:
                        food_listings_with_distance.append(food)
                else:
                    food_listings_with_distance.append(food)
            else:
                food.distance = None
                if not radius_filter:  # Include items without location if no radius filter
                    food_listings_with_distance.append(food)
        
        # Sort by distance (nearest first)
        food_listings_with_distance.sort(key=lambda x: x.distance if x.distance is not None else float('inf'))
        food_listings = food_listings_with_distance
    else:
        # User has no location set, show all listings without distance
        for food in food_listings:
            food.distance = None

    # Get request counts for pipeline
    request_counts = FoodRequest.objects.filter(requester=request.user).values('status').annotate(count=Count('status')).order_by('status')

    # Convert to dict for template
    request_counts_dict = {item['status']: item['count'] for item in request_counts}

    # Prepare food listings JSON for JavaScript
    food_listings_json = json.dumps([
        {
            'id': food.id,
            'expiry_time': food.expiry_time.isoformat(),
            'pickup_location': food.pickup_location,
            'food_name': food.food_name,
            'food_type': food.food_type,
            'quantity': food.quantity,
            'donor': food.donor.username,
            'distance': food.distance if hasattr(food, 'distance') else None
        } for food in food_listings
    ])

    context = {
        'food_listings': food_listings,
        'user_requests': user_requests,
        'completed_requests': completed_requests,
        'food_type': food_type,
        'location': location,
        'expiry_filter': expiry_filter,
        'radius_filter': radius_filter,
        'request_counts': request_counts_dict,
        'food_listings_json': food_listings_json,
    }
    return render(request, 'receiver/dashboard.html', context)

@login_required
def food_detail(request, food_id):
    if request.user.profile.role != 'receiver':
        return redirect('accounts:home')

    food = get_object_or_404(FoodListing, id=food_id, status='available')
    form = FoodRequestForm()

    if request.method == 'POST':
        form = FoodRequestForm(request.POST)
        if form.is_valid():
            food_request = form.save(commit=False)
            food_request.food_listing = food
            food_request.requester = request.user
            if form.cleaned_data.get('needs_delivery'):
                food_request.delivery_status = 'pending_driver'
            else:
                food_request.delivery_status = 'none'
            food_request.save()
            food.status = 'requested'
            food.save()
            messages.success(request, 'Your request has been submitted successfully!')
            return redirect('receiver:dashboard')

    # Check if user has already requested this food
    has_requested = FoodRequest.objects.filter(food_listing=food, requester=request.user).exists()

    # Calculate distance and ETA
    user_profile = request.user.profile
    distance = None
    eta = None

    if user_profile.latitude and user_profile.longitude and food.latitude and food.longitude:
        distance = calculate_distance(
            user_profile.latitude, user_profile.longitude,
            food.latitude, food.longitude
        )
        # Average driving speed of 30 km/h corresponds to 2 minutes per kilometer
        eta = max(1, round(distance * 2))

    context = {
        'food': food,
        'form': form,
        'has_requested': has_requested,
        'distance': distance,
        'eta': eta,
    }
    return render(request, 'receiver/food_detail.html', context)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        rating = request.POST.get('rating')
        feedback_text = request.POST.get('feedback_text', '')

        try:
            food_request = FoodRequest.objects.get(id=request_id, requester=request.user)
            feedback = Feedback.objects.create(
                food_request=food_request,
                receiver=request.user,
                rating=rating,
                feedback_text=feedback_text
            )
            messages.success(request, 'Thank you for your feedback!')
        except FoodRequest.DoesNotExist:
            messages.error(request, 'Request not found.')

    return redirect('receiver:dashboard')

@login_required
def submit_report(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        report_text = request.POST.get('report_text', '')

        try:
            food_request = FoodRequest.objects.get(id=request_id, requester=request.user, status='completed')
            # Check if report already exists
            if hasattr(food_request, 'report'):
                messages.warning(request, 'You have already submitted a report for this request.')
            else:
                report = Report.objects.create(
                    food_request=food_request,
                    reporter=request.user,
                    report_text=report_text
                )
                messages.success(request, 'Your report has been submitted successfully!')
        except FoodRequest.DoesNotExist:
            messages.error(request, 'Request not found or not completed.')

    return redirect('receiver:dashboard')


@login_required
def get_notifications(request):
    """AJAX endpoint to fetch unread notifications for receiver"""
    if request.user.profile.role != 'receiver':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:10]  # Get latest 10 unread notifications
    
    notifications_data = [{
        'id': notif.id,
        'type': notif.notification_type,
        'title': notif.title,
        'message': notif.message,
        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'request_id': notif.related_request.id if notif.related_request else None,
    } for notif in notifications]
    
    return JsonResponse({
        'notifications': notifications_data,
        'count': notifications.count()
    })


@login_required
def get_notification_count(request):
    """AJAX endpoint to get unread notification count for receiver"""
    if request.user.profile.role != 'receiver':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def mark_notification_read(request, notification_id):
    """AJAX endpoint to mark a notification as read for receiver"""
    if request.user.profile.role != 'receiver':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def mark_all_notifications_read(request):
    """AJAX endpoint to mark all notifications as read for receiver"""
    if request.user.profile.role != 'receiver':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def route_map(request):
    if request.user.profile.role != 'receiver':
        return redirect('accounts:home')

    from donor.models import FoodListing
    from django.utils import timezone
    import json

    # Retrieve all available and non-expired food listings that have coordinates
    now = timezone.now()
    food_listings = FoodListing.objects.filter(
        status='available',
        expiry_time__gt=now,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('donor')

    # Get user profile coordinates
    user_profile = request.user.profile
    receiver_lat = float(user_profile.latitude) if user_profile.latitude else None
    receiver_lng = float(user_profile.longitude) if user_profile.longitude else None

    # Calculate distance for each listing from the receiver
    listings_data = []
    for food in food_listings:
        distance = None
        if receiver_lat and receiver_lng:
            from donor.utils import calculate_distance
            distance = calculate_distance(
                receiver_lat, receiver_lng,
                float(food.latitude), float(food.longitude)
            )
        
        # Calculate time remaining in hours
        time_diff = food.expiry_time - now
        hours_remaining = time_diff.total_seconds() / 3600.0

        listings_data.append({
            'id': food.id,
            'food_name': food.food_name,
            'food_type': food.food_type,
            'quantity': food.quantity,
            'donor': food.donor.username,
            'latitude': float(food.latitude),
            'longitude': float(food.longitude),
            'pickup_location': food.pickup_location,
            'hours_remaining': round(hours_remaining, 1),
            'distance': round(distance, 1) if distance is not None else None
        })

    # Sort listings by distance (nearest first)
    if receiver_lat and receiver_lng:
        listings_data.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))

    context = {
        'listings_json': json.dumps(listings_data),
        'receiver_lat': receiver_lat or 28.6139,  # Default to New Delhi if not set
        'receiver_lng': receiver_lng or 77.2090,
    }
    return render(request, 'receiver/route_map.html', context)


@login_required
def batch_claim(request):
    if request.user.profile.role != 'receiver':
        return redirect('accounts:home')

    if request.method == 'POST':
        from donor.models import FoodListing, FoodRequest, Notification
        from django.db import transaction
        from django.utils import timezone
        import datetime

        food_ids_str = request.POST.get('food_ids', '')
        pickup_time_str = request.POST.get('pickup_time', '')
        contact_person = request.POST.get('contact_person', '')
        contact_number = request.POST.get('contact_number', '')
        vehicle_info = request.POST.get('vehicle_info', '')
        needs_delivery = request.POST.get('needs_delivery') == 'true'

        # Parse food IDs
        food_ids = [int(fid.strip()) for fid in food_ids_str.split(',') if fid.strip().isdigit()]

        if not food_ids:
            messages.error(request, 'No food listings selected.')
            return redirect('receiver:route_map')

        # Parse pickup time
        try:
            pickup_time = timezone.make_aware(datetime.datetime.strptime(pickup_time_str, '%Y-%m-%dT%H:%M'))
        except (ValueError, TypeError):
            pickup_time = timezone.now() + datetime.timedelta(hours=2)

        try:
            with transaction.atomic():
                for fid in food_ids:
                    food = FoodListing.objects.select_for_update().get(id=fid, status='available')
                    
                    # Create Food Request
                    food_request = FoodRequest.objects.create(
                        food_listing=food,
                        requester=request.user,
                        status='pending',
                        pickup_time=pickup_time,
                        contact_person=contact_person,
                        contact_number=contact_number,
                        vehicle_info=vehicle_info,
                        delivery_status='pending_driver' if needs_delivery else 'none'
                    )
                    
                    # Update status of food listing to requested
                    food.status = 'requested'
                    food.save()

                    # Send notification to donor
                    Notification.objects.create(
                        recipient=food.donor,
                        notification_type='new_request',
                        title='New Food Request',
                        message=f'{request.user.username} has requested your food listing: {food.food_name}',
                        related_request=food_request
                    )

            messages.success(request, f'Successfully requested {len(food_ids)} food listings!')
            return redirect('receiver:dashboard')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('receiver:route_map')

@login_required
def driver_directory(request):
    if request.user.profile.role != 'receiver':
        return redirect('accounts:home')

    from accounts.models import Profile
    from django.contrib.auth.models import User

    # Get onboarded, verified drivers
    drivers = Profile.objects.filter(
        role='driver', 
        is_driver_onboarded=True, 
        is_verified=True
    ).select_related('user')

    # Approved requests claimed by this NGO that don't have a driver assigned
    eligible_requests = FoodRequest.objects.filter(
        requester=request.user,
        status='approved',
        delivery_status__in=['none', 'pending_driver'],
        driver__isnull=True
    ).select_related('food_listing', 'food_listing__donor')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        driver_id = request.POST.get('driver_id')

        food_req = get_object_or_404(
            FoodRequest, 
            id=request_id, 
            requester=request.user,
            status='approved',
            driver__isnull=True
        )
        driver_user = get_object_or_404(User, id=driver_id, profile__role='driver')

        # Assign driver & set status
        food_req.driver = driver_user
        food_req.delivery_status = 'pending_driver' 
        food_req.save()

        # Send driver notification
        Notification.objects.create(
            recipient=driver_user,
            notification_type='new_request',
            title='Direct Transport Request from NGO',
            message=f'NGO {request.user.username} has requested you specifically to transport "{food_req.food_listing.food_name}" from Donor "{food_req.food_listing.donor.username}" to their center.',
            related_request=food_req
        )

        messages.success(request, f'Direct delivery request sent to driver {driver_user.username} successfully!')
        return redirect('receiver:driver_directory')

    return render(request, 'receiver/driver_directory.html', {
        'drivers': drivers,
        'eligible_requests': eligible_requests
    })
