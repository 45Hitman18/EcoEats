from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FoodListing, FoodRequest, DonorReport, Notification
from .forms import FoodListingForm, DonorReportForm

@login_required
def dashboard(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food_listings = FoodListing.objects.filter(donor=request.user)
    total_food_posted = food_listings.count()
    active_requests = FoodRequest.objects.filter(food_listing__donor=request.user, status__in=['pending', 'approved']).count()
    donated_food_count = food_listings.filter(status='donated').count()
    supported_centers = FoodRequest.objects.filter(
        food_listing__donor=request.user,
        status='completed'
    ).values('requester').distinct().count()

    # Calculate donation increase percentage vs last month
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(seconds=1)

    current_month_donations = food_listings.filter(
        status='donated',
        updated_at__gte=current_month_start
    ).count()
    last_month_donations = food_listings.filter(
        status='donated',
        updated_at__gte=last_month_start,
        updated_at__lte=last_month_end
    ).count()

    if last_month_donations > 0:
        donation_increase_percentage = round(((current_month_donations - last_month_donations) / last_month_donations) * 100)
    else:
        donation_increase_percentage = 0 if current_month_donations == 0 else 100

    # Get expiring soon food (within 24 hours)
    from django.utils import timezone
    from datetime import timedelta
    expiring_soon = food_listings.filter(
        expiry_time__lte=timezone.now() + timedelta(hours=24),
        status='available'
    )

    # Get recent activity (last 5 food listings)
    recent_activity = food_listings.order_by('-created_at')[:5]

    context = {
        'food_listings': food_listings,
        'total_food_posted': total_food_posted,
        'active_requests': active_requests,
        'donated_food_count': donated_food_count,
        'supported_centers': supported_centers,
        'donation_increase_percentage': donation_increase_percentage,
        'expiring_soon': expiring_soon,
        'recent_activity': recent_activity,
    }
    return render(request, 'donor/dashboard.html', context)

@login_required
def add_food(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    if request.method == 'POST':
        form = FoodListingForm(request.POST)
        if form.is_valid():
            food_listing = form.save(commit=False)
            food_listing.donor = request.user

            # Handle location fields from JavaScript
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            pickup_location = request.POST.get('pickup_location')

            if latitude and longitude:
                food_listing.latitude = float(latitude)
                food_listing.longitude = float(longitude)
                food_listing.pickup_location = pickup_location or f"{latitude}, {longitude}"

            food_listing.save()

            # Notify NGO receivers about new food listing
            from accounts.models import Profile
            receivers = Profile.objects.filter(role='receiver').select_related('user')
            for receiver in receivers:
                Notification.objects.create(
                    recipient=receiver.user,
                    notification_type='new_request',
                    title='New Surplus Food Available',
                    message=f'A new surplus food listing "{food_listing.food_name}" ({food_listing.quantity} kg) is now available at "{food_listing.pickup_location}". Claim it now!',
                )

            messages.success(request, 'Food listing added successfully!')
            return redirect('donor:dashboard')
    else:
        form = FoodListingForm()

    context = {
        'form': form,
    }
    return render(request, 'donor/add_food.html', context)

@login_required
def manage_food(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food_listings = FoodListing.objects.filter(donor=request.user, is_deleted=False)
    context = {
        'food_listings': food_listings,
    }
    return render(request, 'donor/manage_food.html', context)

@login_required
def bulk_manage_food(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_listings')
        action = request.POST.get('action')
        
        if not selected_ids:
            messages.warning(request, "No listings selected.")
            return redirect('donor:manage_food')

        listings = FoodListing.objects.filter(id__in=selected_ids, donor=request.user)
        
        if action == 'expire':
            listings.update(status='expired')
            messages.success(request, f"Successfully marked {listings.count()} listings as expired.")
        elif action == 'delete':
            listings.update(is_deleted=True)
            messages.success(request, f"Successfully deleted {listings.count()} listings.")

    return redirect('donor:manage_food')

@login_required
def view_requests(request, food_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food = get_object_or_404(FoodListing, id=food_id, donor=request.user)
    requests = FoodRequest.objects.filter(food_listing=food)
    context = {
        'food': food,
        'requests': requests,
    }
    return render(request, 'donor/view_requests.html', context)

@login_required
def view_all_requests(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    requests = FoodRequest.objects.filter(food_listing__donor=request.user).order_by('-requested_at')
    context = {
        'requests': requests,
    }
    return render(request, 'donor/view_all_requests.html', context)

@login_required
def mark_expired(request, food_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food = get_object_or_404(FoodListing, id=food_id, donor=request.user)
    food.status = 'expired'
    food.save()
    messages.success(request, 'Food marked as expired.')
    return redirect('donor:manage_food')

@login_required
def delete_food(request, food_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food = get_object_or_404(FoodListing, id=food_id, donor=request.user)
    food.delete()
    messages.success(request, 'Food listing deleted.')
    return redirect('donor:manage_food')

@login_required
def approve_request(request, request_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food_request = get_object_or_404(FoodRequest, id=request_id, food_listing__donor=request.user)
    food_request.status = 'approved'
    food_request.save()
    messages.success(request, 'Request approved successfully!')
    return redirect('donor:view_requests', food_id=food_request.food_listing.id)

@login_required
def reject_request(request, request_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food_request = get_object_or_404(FoodRequest, id=request_id, food_listing__donor=request.user)
    food_request.status = 'rejected'
    food_request.save()
    messages.success(request, 'Request rejected.')
    return redirect('donor:view_requests', food_id=food_request.food_listing.id)

@login_required
def complete_request(request, request_id):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    food_request = get_object_or_404(FoodRequest, id=request_id, food_listing__donor=request.user)
    food_request.status = 'completed'
    food_request.save()
    # Optionally mark the food listing as donated if all requests are completed
    food_listing = food_request.food_listing
    if not food_listing.requests.filter(status__in=['pending', 'approved']).exists():
        food_listing.status = 'donated'
        food_listing.save()
    messages.success(request, 'Request marked as completed!')
    return redirect('donor:view_requests', food_id=food_request.food_listing.id)

@login_required
def view_feedback(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from receiver.models import Feedback
    feedback_list = Feedback.objects.filter(
        food_request__food_listing__donor=request.user
    ).select_related('food_request__food_listing', 'receiver').order_by('-created_at')

    context = {
        'feedback_list': feedback_list,
    }
    return render(request, 'donor/view_feedback.html', context)

@login_required
def submit_report(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        report_text = request.POST.get('report_text', '')

        try:
            food_request = FoodRequest.objects.get(id=request_id, food_listing__donor=request.user, status='completed')
            # Check if report already exists
            if DonorReport.objects.filter(food_request=food_request).exists():
                messages.warning(request, 'You have already submitted a report for this request.')
            else:
                report = DonorReport.objects.create(
                    food_request=food_request,
                    reporter=request.user,
                    report_text=report_text
                )
                messages.success(request, 'Your report has been submitted successfully!')
        except FoodRequest.DoesNotExist:
            messages.error(request, 'Request not found or not completed.')

    return redirect('donor:manage_food')


@login_required
def get_notifications(request):
    """AJAX endpoint to fetch unread notifications for the current user"""
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
    """AJAX endpoint to get unread notification count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def mark_notification_read(request, notification_id):
    """AJAX endpoint to mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def mark_all_notifications_read(request):
    """AJAX endpoint to mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def donor_analytics(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from django.db.models import Sum, Count
    from django.db.models.functions import ExtractMonth, ExtractYear
    from django.utils import timezone
    import datetime
    import json
    from donor.models import FoodListing, FoodRequest

    # 1. Total Metrics
    donated_listings = FoodListing.objects.filter(donor=request.user, status='donated')
    total_quantity = donated_listings.aggregate(total=Sum('quantity'))['total'] or 0

    meals_distributed = total_quantity
    co2_saved = total_quantity * 2.5 # 2.5 kg CO2 per unit
    value_saved = total_quantity * 50.0 # ₹50 per unit/serving (approx value in INR)

    # Supported Centers Count
    supported_centers_count = FoodRequest.objects.filter(
        food_listing__donor=request.user,
        status='completed'
    ).values('requester').distinct().count()

    # 2. Monthly Performance for Chart.js
    monthly_data = (
        donated_listings
        .annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at'))
        .values('year', 'month')
        .annotate(total_qty=Sum('quantity'))
        .order_by('year', 'month')
    )

    # Get last 6 months list
    last_six_months = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        d = datetime.date(year, month, 1)
        last_six_months.append((year, month, d.strftime('%b')))

    # Build a mapping from (year, month) to total_qty
    monthly_map = {(item['year'], item['month']): item['total_qty'] for item in monthly_data}

    # Prepare data for Chart.js
    chart_labels = []
    chart_data = []
    for yr, mo, name in last_six_months:
        chart_labels.append(f"{name} {yr}")
        chart_data.append(monthly_map.get((yr, mo), 0))

    # 3. Top Supported Organizations
    top_organizations = (
        FoodRequest.objects.filter(food_listing__donor=request.user, status='completed')
        .values('requester__username')
        .annotate(total_servings=Sum('food_listing__quantity'), count=Count('id'))
        .order_by('-total_servings')[:5]
    )

    context = {
        'total_quantity': total_quantity,
        'meals_distributed': meals_distributed,
        'co2_saved': co2_saved,
        'value_saved': value_saved,
        'supported_centers_count': supported_centers_count,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
        'top_organizations': top_organizations,
    }
    return render(request, 'donor/analytics.html', context)


@login_required
def ngo_directory(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from accounts.models import Profile
    from donor.models import FoodListing
    from donor.utils import calculate_distance
    from django.db.models import Q

    # Get search and filter parameters
    q = request.GET.get('q', '')
    is_verified = request.GET.get('is_verified') == 'on'
    has_fridge = request.GET.get('has_fridge') == 'on'
    has_freezer = request.GET.get('has_freezer') == 'on'
    has_warmers = request.GET.get('has_warmers') == 'on'

    # Filter receiver profiles
    profiles = Profile.objects.filter(role='receiver').select_related('user')

    if q:
        profiles = profiles.filter(
            Q(user__username__icontains=q) | 
            Q(user__first_name__icontains=q) | 
            Q(user__last_name__icontains=q) |
            Q(location__icontains=q)
        )
    
    if is_verified:
        profiles = profiles.filter(is_verified=True)
    if has_fridge:
        profiles = profiles.filter(has_fridge=True)
    if has_freezer:
        profiles = profiles.filter(has_freezer=True)
    if has_warmers:
        profiles = profiles.filter(has_warmers=True)

    donor_profile = request.user.profile
    donor_lat = float(donor_profile.latitude) if donor_profile.latitude else None
    donor_lng = float(donor_profile.longitude) if donor_profile.longitude else None

    # Calculate distance for each NGO profile
    ngo_list = []
    for prof in profiles:
        distance = None
        if donor_lat and donor_lng and prof.latitude and prof.longitude:
            distance = calculate_distance(
                donor_lat, donor_lng,
                float(prof.latitude), float(prof.longitude)
            )

        ngo_list.append({
            'profile': prof,
            'distance': round(distance, 1) if distance is not None else None
        })

    # Sort NGOs by distance (nearest first)
    if donor_lat and donor_lng:
        ngo_list.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))

    # Fetch donor's active available listings to populate allocation modals
    available_listings = FoodListing.objects.filter(donor=request.user, status='available')

    context = {
        'ngo_list': ngo_list,
        'available_listings': available_listings,
        'search_query': q,
        'is_verified': is_verified,
        'has_fridge': has_fridge,
        'has_freezer': has_freezer,
        'has_warmers': has_warmers,
    }
    return render(request, 'donor/ngo_directory.html', context)


@login_required
def allocate_food(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    if request.method == 'POST':
        from donor.models import FoodListing, FoodRequest, Notification
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        import datetime

        food_id = request.POST.get('food_id')
        receiver_id = request.POST.get('receiver_id')
        pickup_time_str = request.POST.get('pickup_time', '')

        # Get food listing
        food = get_object_or_404(FoodListing, id=food_id, donor=request.user, status='available')
        
        # Get receiver profile
        User = get_user_model()
        receiver = get_object_or_404(User, id=receiver_id, profile__role='receiver')

        # Parse pickup time
        try:
            pickup_time = timezone.make_aware(datetime.datetime.strptime(pickup_time_str, '%Y-%m-%dT%H:%M'))
        except (ValueError, TypeError):
            pickup_time = food.expiry_time

        # Create FoodRequest pre-approved
        food_request = FoodRequest.objects.create(
            food_listing=food,
            requester=receiver,
            status='approved',  # Pre-approved by donor allocation
            pickup_time=pickup_time,
            contact_person=request.user.username,
            contact_number=request.user.profile.phone,
            vehicle_info="TBD by NGO (Direct Offer Allocation)"
        )

        # Update food listing status
        food.status = 'requested'
        food.save()

        # Send notification to NGO receiver
        Notification.objects.create(
            recipient=receiver,
            notification_type='new_request',
            title='Direct Food Offer Allocation',
            message=f'{request.user.username} has directly allocated a food listing to you: {food.food_name}. It is pre-approved for pickup!',
            related_request=food_request
        )

        messages.success(request, f'Successfully allocated "{food.food_name}" directly to {receiver.username}!')
        return redirect('donor:ngo_directory')

    return redirect('donor:ngo_directory')


@login_required
def broadcast_alert(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    if request.method == 'POST':
        from donor.models import FoodListing, Notification
        from donor.utils import calculate_distance
        from accounts.models import Profile

        food_id = request.POST.get('food_id')
        food = get_object_or_404(FoodListing, id=food_id, donor=request.user, status='available')

        donor_profile = request.user.profile
        donor_lat = float(donor_profile.latitude) if donor_profile.latitude else None
        donor_lng = float(donor_profile.longitude) if donor_profile.longitude else None

        if not donor_lat or not donor_lng:
            messages.error(request, 'Please configure your location coordinates in your profile to broadcast alerts.')
            return redirect('donor:ngo_directory')

        # Find all NGOs within 3km radius
        receivers = Profile.objects.filter(role='receiver', latitude__isnull=False, longitude__isnull=False)
        alerted_count = 0

        for r_profile in receivers:
            dist = calculate_distance(donor_lat, donor_lng, float(r_profile.latitude), float(r_profile.longitude))
            if dist <= 3.0:
                Notification.objects.create(
                    recipient=r_profile.user,
                    notification_type='alert',
                    title='URGENT: Nearby Surplus Food Alert',
                    message=f'URGENT: {request.user.username} has a food listing "{food.food_name}" expiring soon within 3km of you! Claim it immediately.',
                    related_request=None
                )
                alerted_count += 1

        if alerted_count > 0:
            messages.success(request, f'Urgent broadcast alert sent to {alerted_count} nearby organizations within 3km!')
        else:
            messages.info(request, 'No verified organizations found within a 3.0 km radius of your location.')

        return redirect('donor:ngo_directory')

    return redirect('donor:ngo_directory')

@login_required
def csr_impact(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    import json
    from django.utils import timezone
    from datetime import timedelta

    # 1. Total rescued statistics
    donated_listings = FoodListing.objects.filter(donor=request.user, status='donated')
    total_weight = donated_listings.aggregate(total=Sum('quantity'))['total'] or 0

    # 2. Sustainability metrics formulas
    co2_offset = round(total_weight * 2.5, 1) # 2.5kg CO2 per 1kg food
    water_saved = round(total_weight * 1000)   # 1000L water per 1kg food
    meals_provided = round(total_weight / 0.4) # 0.4kg per meal

    # 3. Monthly donation impact history (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_impacts = (
        donated_listings.filter(updated_at__gte=six_months_ago)
        .annotate(month=TruncMonth('updated_at'))
        .values('month')
        .annotate(weight=Sum('quantity'))
        .order_by('month')
    )

    chart_labels = []
    chart_values = []
    for item in monthly_impacts:
        chart_labels.append(item['month'].strftime('%B %Y'))
        chart_values.append(float(item['weight'] or 0))

    # 4. Certifications
    certification_tier = "Standard Partner"
    cert_badge_color = "bg-secondary text-white"
    cert_icon = "fa-handshake"
    
    if total_weight >= 500:
        certification_tier = "Emerald Zero-Waste Champion"
        cert_badge_color = "bg-success text-white"
        cert_icon = "fa-crown"
    elif total_weight >= 250:
        certification_tier = "Gold Eco Pioneer"
        cert_badge_color = "bg-warning text-dark"
        cert_icon = "fa-award"
    elif total_weight >= 100:
        certification_tier = "Silver Food Rescuer"
        cert_badge_color = "bg-light text-dark"
        cert_icon = "fa-shield-halved"
    elif total_weight >= 10:
        certification_tier = "Bronze Eco Contributor"
        cert_badge_color = "bg-bronze text-white"
        cert_icon = "fa-seedling"

    # Fallback to display empty/minimal graphs if no history yet
    if not chart_labels:
        chart_labels = ["Last Month", "This Month"]
        chart_values = [0, total_weight]

    context = {
        'total_weight': total_weight,
        'co2_offset': co2_offset,
        'water_saved': water_saved,
        'meals_provided': meals_provided,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'certification_tier': certification_tier,
        'cert_badge_color': cert_badge_color,
        'cert_icon': cert_icon,
        'today_date': timezone.now().strftime('%B %d, %Y')
    }
    return render(request, 'donor/csr_impact.html', context)

@login_required
def generate_csr_certificate(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from django.db.models import Sum
    from django.utils import timezone
    import hashlib

    # Calculate metrics
    donated_listings = FoodListing.objects.filter(donor=request.user, status='donated')
    total_weight = donated_listings.aggregate(total=Sum('quantity'))['total'] or 0

    co2_offset = round(total_weight * 2.5, 1)
    water_saved = round(total_weight * 1000)
    meals_provided = round(total_weight / 0.4)

    # Determine certification tier
    certification_tier = "Standard Partner"
    if total_weight >= 500:
        certification_tier = "Emerald Zero-Waste Champion"
    elif total_weight >= 250:
        certification_tier = "Gold Eco Pioneer"
    elif total_weight >= 100:
        certification_tier = "Silver Food Rescuer"
    elif total_weight >= 10:
        certification_tier = "Bronze Eco Contributor"

    # Generate a unique serial verification hash
    hash_input = f"{request.user.username}-{total_weight}-{timezone.now().strftime('%Y%m%d')}"
    cert_code = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12].upper()

    context = {
        'total_weight': total_weight,
        'co2_offset': co2_offset,
        'water_saved': water_saved,
        'meals_provided': meals_provided,
        'certification_tier': certification_tier,
        'cert_code': f"EE-CSR-{cert_code}",
        'today_date': timezone.now().strftime('%B %d, %Y'),
        'org_name': request.user.profile.organization_name or request.user.username
    }
    return render(request, 'donor/csr_certificate.html', context)

@login_required
def driver_directory(request):
    if request.user.profile.role != 'donor':
        return redirect('accounts:home')

    from accounts.models import Profile

    # Get onboarded, verified drivers
    drivers = Profile.objects.filter(
        role='driver', 
        is_driver_onboarded=True, 
        is_verified=True
    ).select_related('user')

    # Approved requests submitted for donor's listings that don't have driver assigned
    eligible_requests = FoodRequest.objects.filter(
        food_listing__donor=request.user,
        status='approved',
        delivery_status__in=['none', 'pending_driver'],
        driver__isnull=True
    ).select_related('food_listing', 'requester')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        driver_id = request.POST.get('driver_id')

        from django.contrib.auth.models import User
        food_req = get_object_or_404(
            FoodRequest, 
            id=request_id, 
            food_listing__donor=request.user,
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
            title='Direct Transport Request',
            message=f'Donor {request.user.username} has requested you specifically to transport "{food_req.food_listing.food_name}" to NGO "{food_req.requester.username}".',
            related_request=food_req
        )

        messages.success(request, f'Direct delivery request sent to driver {driver_user.username} successfully!')
        return redirect('donor:driver_directory')

    return render(request, 'donor/driver_directory.html', {
        'drivers': drivers,
        'eligible_requests': eligible_requests
    })


import logging
import os
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('donor.ml')

@csrf_exempt
@login_required
def predict_shelf_life(request):
    if request.user.profile.role != 'donor':
        return JsonResponse({'error': 'Access denied.'}, status=403)

    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
            
        category = data.get('category')
        prep_time_str = data.get('prepared_time')
        temperature_str = data.get('temperature')
        packaging = data.get('packaging')
        
        # 1. Validation
        valid_categories = ['veg', 'non-veg', 'bakery', 'cooked', 'dairy']
        valid_packaging = ['airtight', 'boxed', 'open', 'refrigerated']
        
        if not category or category not in valid_categories:
            return JsonResponse({'error': 'Invalid or missing food category.'}, status=400)
            
        if not packaging or packaging not in valid_packaging:
            return JsonResponse({'error': 'Invalid or missing packaging type.'}, status=400)
            
        try:
            temperature = float(temperature_str)
            if not (0 <= temperature <= 50):
                raise ValueError()
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Temperature must be a number between 0 and 50 °C.'}, status=400)
            
        if not prep_time_str:
            return JsonResponse({'error': 'Missing preparation time.'}, status=400)
            
        prepared_time = parse_datetime(prep_time_str)
        if not prepared_time:
            return JsonResponse({'error': 'Invalid preparation time format.'}, status=400)
            
        # Ensure timezone-aware comparison
        from django.utils import timezone
        now = timezone.now()
        
        # Handle timezone conversion if prepared_time is naive
        if timezone.is_naive(prepared_time):
            prepared_time = timezone.make_aware(prepared_time, timezone.get_default_timezone())
            
        if prepared_time > now:
            return JsonResponse({'error': 'Preparation time cannot be in the future.'}, status=400)
            
        # Calculate prep age in hours
        time_diff = now - prepared_time
        prep_age_hours = time_diff.total_seconds() / 3600.0
        
        if prep_age_hours > 72:
            return JsonResponse({'error': 'Preparation time is too far in the past (must be within 72 hours).'}, status=400)

        # 2. Retrieve Model
        from .apps import DonorConfig
        model = DonorConfig.model
        feature_columns = DonorConfig.feature_columns
        
        # Fallback lazy loading
        if not model:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.abspath(os.path.join(base_dir, '../ml_assets/shelf_life_model.joblib'))
            if os.path.exists(model_path):
                try:
                    import joblib
                    payload = joblib.load(model_path)
                    model = payload.get('model')
                    feature_columns = payload.get('feature_columns')
                except Exception as e:
                    logger.error(f"Error lazy-loading ML model: {str(e)}")
            
        if not model:
            return JsonResponse({'error': 'Machine learning model is not available.'}, status=503)
            
        # 3. Features One-Hot Encoding
        try:
            input_dict = {col: 0.0 for col in feature_columns}
            
            # Numeric values
            input_dict['prep_age_hours'] = prep_age_hours
            input_dict['temperature'] = temperature
            
            # Category
            cat_col = f"category_{category}"
            if cat_col in input_dict:
                input_dict[cat_col] = 1.0
                
            # Packaging
            pack_col = f"packaging_{packaging}"
            if pack_col in input_dict:
                input_dict[pack_col] = 1.0
                
            # Ordered input features
            input_vector = [input_dict[col] for col in feature_columns]
            
            # 4. Predict
            prediction = model.predict([input_vector])
            predicted_hours = float(prediction[0])
            
            recommended_expiry = now + timezone.timedelta(hours=predicted_hours)
            expiry_str = recommended_expiry.strftime('%Y-%m-%dT%H:%M')
            
            logger.info(
                f"ML prediction - Category: {category}, Temp: {temperature}C, "
                f"Pack: {packaging}, Prep Age: {prep_age_hours:.1f}h. "
                f"Predicted shelf-life: {predicted_hours:.1f}h. Rec Expiry: {expiry_str}"
            )
            
            return JsonResponse({
                'success': True,
                'predicted_shelf_life_hours': round(predicted_hours, 1),
                'recommended_expiry_time': expiry_str
            })
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return JsonResponse({'error': f"Prediction execution failed: {str(e)}"}, status=500)
            
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

