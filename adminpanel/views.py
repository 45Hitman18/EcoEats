from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
import json
from accounts.models import Profile, ActivityLog


def _ensure_profile(user: User) -> Profile:
    """Return the user's profile, creating a minimal one if missing."""
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            "phone": "",
            "location": "",
            "role": "receiver",
            "is_verified": False,
        },
    )
    return profile
from donor.models import FoodListing, FoodRequest
from .models import ContactInquiry

@login_required
def dashboard(request):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    # Statistics
    total_users = User.objects.count()
    total_food_saved = FoodRequest.objects.filter(status='completed').count()
    active_donations = FoodListing.objects.filter(status__in=['available', 'requested']).count()

    # Analytics data for last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Food saved per day
    food_saved_data = FoodRequest.objects.filter(
        status='completed',
        requested_at__date__gte=start_date,
        requested_at__date__lte=end_date
    ).annotate(date=TruncDate('requested_at')).values('date').annotate(count=Count('id')).order_by('date')

    food_saved_labels = []
    food_saved_values = []
    current_date = start_date
    while current_date <= end_date:
        food_saved_labels.append(current_date.strftime('%Y-%m-%d'))
        count = next((item['count'] for item in food_saved_data if item['date'] == current_date), 0)
        food_saved_values.append(count)
        current_date += timedelta(days=1)

    # Donation trends per day
    donation_data = FoodListing.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')

    donation_trends_labels = []
    donation_trends_values = []
    current_date = start_date
    while current_date <= end_date:
        donation_trends_labels.append(current_date.strftime('%Y-%m-%d'))
        count = next((item['count'] for item in donation_data if item['date'] == current_date), 0)
        donation_trends_values.append(count)
        current_date += timedelta(days=1)

    # Fetch pending verification requests (profiles that are NOT verified and NOT admin)
    pending_verifications = Profile.objects.filter(is_verified=False).exclude(role='admin').select_related('user')[:5]

    context = {
        'total_users': total_users,
        'total_food_saved': total_food_saved,
        'active_donations': active_donations,
        'food_saved_labels': json.dumps(food_saved_labels),
        'food_saved_values': json.dumps(food_saved_values),
        'donation_trends_labels': json.dumps(donation_trends_labels),
        'donation_trends_values': json.dumps(donation_trends_values),
        'pending_verifications': pending_verifications,
    }
    return render(request, 'adminpanel/dashboard.html', context)

@login_required
def view_users(request):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    users = list(User.objects.select_related('profile').all())
    # Backfill any missing profiles to avoid RelatedObjectDoesNotExist in templates
    for user in users:
        _ensure_profile(user)
    context = {
        'users': users,
    }
    return render(request, 'adminpanel/view_users.html', context)

@login_required
def toggle_user_status(request, user_id):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    user = get_object_or_404(User, id=user_id)
    profile = _ensure_profile(user)

    if profile.is_verified:
        profile.is_verified = False
        messages.success(request, f'User {user.username} has been blocked.')
    else:
        profile.is_verified = True
        messages.success(request, f'User {user.username} has been verified.')

    profile.save()
    
    # Check referer to redirect back to dashboard if applicable
    referer = request.META.get('HTTP_REFERER')
    if referer and 'adminpanel' in referer and 'users' not in referer:
        return redirect('adminpanel:dashboard')
    return redirect('adminpanel:view_users')

@login_required
def user_detail(request, user_id):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    user = get_object_or_404(User, id=user_id)
    profile = _ensure_profile(user)

    # Get user's food listings (if donor)
    food_listings = FoodListing.objects.filter(donor=user).select_related('donor')

    # Get user's food requests (if receiver)
    food_requests = FoodRequest.objects.filter(requester=user).select_related('food_listing__donor')

    # Get driver's delivery runs (if driver)
    driver_deliveries = FoodRequest.objects.filter(driver=user).select_related('food_listing', 'food_listing__donor', 'requester')

    # Get user's activity logs
    activity_logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:10]  # Last 10 activities

    context = {
        'user': user,
        'profile': profile,
        'food_listings': food_listings,
        'food_requests': food_requests,
        'driver_deliveries': driver_deliveries,
        'activity_logs': activity_logs,
    }
    return render(request, 'adminpanel/user_detail.html', context)

@login_required
def view_food_listings(request):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    from .forms import FoodListingFilterForm

    food_listings = FoodListing.objects.select_related('donor').all()
    filter_form = FoodListingFilterForm(request.GET)

    if filter_form.is_valid():
        # Apply filters
        food_name = filter_form.cleaned_data.get('food_name')
        if food_name:
            food_listings = food_listings.filter(food_name__icontains=food_name)

        food_type = filter_form.cleaned_data.get('food_type')
        if food_type:
            food_listings = food_listings.filter(food_type=food_type)

        status = filter_form.cleaned_data.get('status')
        if status:
            food_listings = food_listings.filter(status=status)

        donor = filter_form.cleaned_data.get('donor')
        if donor:
            food_listings = food_listings.filter(donor=donor)

        min_quantity = filter_form.cleaned_data.get('min_quantity')
        if min_quantity is not None:
            food_listings = food_listings.filter(quantity__gte=min_quantity)

        max_quantity = filter_form.cleaned_data.get('max_quantity')
        if max_quantity is not None:
            food_listings = food_listings.filter(quantity__lte=max_quantity)

        expiry_from = filter_form.cleaned_data.get('expiry_from')
        if expiry_from:
            food_listings = food_listings.filter(expiry_time__gte=expiry_from)

        expiry_to = filter_form.cleaned_data.get('expiry_to')
        if expiry_to:
            food_listings = food_listings.filter(expiry_time__lte=expiry_to)

        pickup_location = filter_form.cleaned_data.get('pickup_location')
        if pickup_location:
            food_listings = food_listings.filter(pickup_location__icontains=pickup_location)

    context = {
        'food_listings': food_listings,
        'filter_form': filter_form,
    }
    return render(request, 'adminpanel/view_food_listings.html', context)

@login_required
def promote_to_admin(request, user_id):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    user = get_object_or_404(User, id=user_id)
    profile = _ensure_profile(user)

    if profile.role != 'admin':
        profile.role = 'admin'
        profile.save()
        messages.success(request, f'User {user.username} has been promoted to admin.')
    else:
        messages.warning(request, f'User {user.username} is already an admin.')

    return redirect('adminpanel:view_users')


@login_required
def delete_user(request, user_id):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} has been deleted from EcoEats.')
        
        # Check referer to redirect back to dashboard if applicable
        referer = request.META.get('HTTP_REFERER')
        if referer and 'adminpanel' in referer and 'users' not in referer:
            return redirect('adminpanel:dashboard')
        return redirect('adminpanel:view_users')

    messages.error(request, 'Invalid request method for deleting user.')
    return redirect('adminpanel:view_users')

@login_required
def view_reports(request):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    from receiver.models import Report
    from donor.models import DonorReport

    receiver_reports = Report.objects.select_related('food_request__food_listing__donor', 'reporter').all()
    donor_reports = DonorReport.objects.select_related('food_request__food_listing__donor', 'reporter').all()

    # Combine both types of reports
    reports = []
    for report in receiver_reports:
        reports.append({
            'id': report.id,
            'reporter': report.reporter,
            'reported_user': report.food_request.food_listing.donor,
            'report_text': report.report_text,
            'created_at': report.created_at,
            'food_name': report.food_request.food_listing.food_name,
            'food_type': report.food_request.food_listing.get_food_type_display(),
            'quantity': report.food_request.food_listing.quantity,
            'type': 'receiver_report'
        })

    for report in donor_reports:
        reports.append({
            'id': report.id,
            'reporter': report.reporter,
            'reported_user': report.food_request.requester,
            'report_text': report.report_text,
            'created_at': report.created_at,
            'food_name': report.food_request.food_listing.food_name,
            'food_type': report.food_request.food_listing.get_food_type_display(),
            'quantity': report.food_request.food_listing.quantity,
            'type': 'donor_report'
        })

    # Sort by creation date
    reports.sort(key=lambda x: x['created_at'], reverse=True)

    context = {
        'reports': reports,
    }
    return render(request, 'adminpanel/view_reports.html', context)

@login_required
def view_inquiries(request):
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    inquiries = ContactInquiry.objects.all().order_by('-submitted_at')

    # Calculate statistics
    from django.utils import timezone
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    # Total inquiries
    total_inquiries = inquiries.count()

    # This month's inquiries
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = current_month.replace(month=current_month.month + 1) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1)
    this_month_inquiries = inquiries.filter(submitted_at__gte=current_month, submitted_at__lt=next_month).count()

    # Restaurant inquiries
    restaurant_inquiries = inquiries.filter(organization_type='restaurant').count()

    context = {
        'inquiries': inquiries,
        'total_inquiries': total_inquiries,
        'this_month_inquiries': this_month_inquiries,
        'restaurant_inquiries': restaurant_inquiries,
    }
    return render(request, 'adminpanel/view_inquiries.html', context)

@login_required
def export_database_backup(request):
    import os
    from django.http import FileResponse, Http404
    from django.conf import settings
    from datetime import datetime

    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    db_path = settings.BASE_DIR / 'db.sqlite3'
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = FileResponse(open(db_path, 'rb'), content_type='application/x-sqlite3')
        response['Content-Disposition'] = f'attachment; filename="ecoeats_backup_{timestamp}.sqlite3"'
        return response
    raise Http404("Database file not found.")

@login_required
def flush_system_caches(request):
    from django.core.cache import cache
    
    admin_profile = _ensure_profile(request.user)
    if admin_profile.role != 'admin':
        return redirect('accounts:home')

    cache.clear()
    messages.success(request, 'System caches have been successfully flushed.')
    return redirect('adminpanel:dashboard')
