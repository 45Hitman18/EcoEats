from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm
from .models import Profile, ActivityLog

def get_client_ip(request):
    """Get the client IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home_view(request):
    from django.db.models import Sum
    from donor.models import FoodListing, FoodRequest
    from accounts.models import Profile

    # Calculate global platform stats
    total_quantity = FoodListing.objects.filter(status='donated').aggregate(total=Sum('quantity'))['total'] or 0
    total_partners = Profile.objects.filter(is_verified=True).count()
    co2_offset = total_quantity * 2.5 # in kg

    # Format numbers nicely
    def format_qty(val):
        if val >= 1000:
            return f"{round(val / 1000, 1)}K+"
        return f"{val} servings"

    def format_co2(val):
        if val >= 1000:
            return f"{round(val / 1000, 1)} Tonnes"
        return f"{val} kg"

    total_quantity_str = format_qty(total_quantity)
    co2_offset_str = format_co2(co2_offset)

    community_centers_supported = 0
    if request.user.is_authenticated:
        try:
            if request.user.profile.role == 'donor':
                community_centers_supported = FoodRequest.objects.filter(
                    food_listing__donor=request.user,
                    status='completed'
                ).values('requester').distinct().count()
        except Exception:
            pass

    context = {
        'total_quantity_str': total_quantity_str,
        'total_partners': total_partners,
        'co2_offset_str': co2_offset_str,
        'community_centers_supported': community_centers_supported
    }
    return render(request, 'home.html', context)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Log registration activity
            ActivityLog.objects.create(
                user=user,
                action='User Registration',
                description=f'New user {user.username} registered',
                action_type='register',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return redirect('accounts:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                try:
                    if not user.profile.is_verified:
                        messages.error(request, 'Your account has been blocked. Please contact support.')
                        return render(request, 'accounts/login.html', {'form': form})
                except Profile.DoesNotExist:
                    messages.error(request, 'Your account has been blocked. Please contact support.')
                    return render(request, 'accounts/login.html', {'form': form})
                login(request, user)
                # Log login activity
                ActivityLog.objects.create(
                    user=user,
                    action='User Login',
                    description=f'User {user.username} logged in',
                    action_type='login',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return redirect('accounts:dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:home')

@login_required
def dashboard_view(request):
    try:
        profile = request.user.profile
    except:
        # If profile doesn't exist, redirect to profile creation
        return redirect('accounts:create_profile')
    
    if profile.role == 'donor':
        return redirect('donor:dashboard')
    elif profile.role == 'receiver':
        return redirect('receiver:dashboard')
    elif profile.role == 'driver':
        return redirect('driver:dashboard')
    elif profile.role == 'admin':
        return redirect('adminpanel:dashboard')
    else:
        return redirect('/')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('accounts:create_profile')

    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('accounts:create_profile')

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Log profile update activity
            ActivityLog.objects.create(
                user=request.user,
                action='Profile Updated',
                description=f'User {request.user.username} updated their profile',
                action_type='profile_updated',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {'profile': profile, 'form': form})

@login_required
def create_profile_view(request):
    if hasattr(request.user, 'profile'):
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        location = request.POST.get('location')
        if phone and role and location:
            Profile.objects.create(user=request.user, phone=phone, role=role, location=location)
            messages.success(request, 'Profile created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'accounts/create_profile.html')
