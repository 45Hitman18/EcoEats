from django.shortcuts import render
from django.contrib import messages
from adminpanel.models import ContactInquiry

def how_it_works(request):
    return render(request, 'how_it_works.html')

def faqs(request):
    return render(request, 'faqs.html')

def about_us(request):
    return render(request, 'about_us.html')

def contact_sales(request):
    if request.method == 'POST':
        # Save the inquiry
        inquiry = ContactInquiry.objects.create(
            full_name=request.POST.get('full_name'),
            organization_name=request.POST.get('organization_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            organization_type=request.POST.get('organization_type'),
            donation_size=request.POST.get('donation_size'),
            location=request.POST.get('location'),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Thank you for your inquiry! Our team will get back to you shortly.')
        return render(request, 'contact_sales.html')
    return render(request, 'contact_sales.html')


def leaderboard(request):
    from django.db.models import Sum
    from django.utils import timezone
    import datetime
    from donor.models import FoodListing, FoodRequest
    from accounts.models import Profile

    now = timezone.now()
    # Start of this month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 1. Donors Leaderboard (This Month)
    donor_leaderboard_month = (
        FoodListing.objects.filter(status='donated', created_at__gte=start_of_month)
        .values('donor')
        .annotate(total_saved=Sum('quantity'))
        .order_by('-total_saved')[:10]
    )

    # 2. Receivers Leaderboard (This Month)
    receiver_leaderboard_month = (
        FoodRequest.objects.filter(status='completed', requested_at__gte=start_of_month)
        .values('requester')
        .annotate(total_claimed=Sum('food_listing__quantity'))
        .order_by('-total_claimed')[:10]
    )

    # 3. Donors Leaderboard (All-Time)
    donor_leaderboard_alltime = (
        FoodListing.objects.filter(status='donated')
        .values('donor')
        .annotate(total_saved=Sum('quantity'))
        .order_by('-total_saved')[:10]
    )

    # 4. Receivers Leaderboard (All-Time)
    receiver_leaderboard_alltime = (
        FoodRequest.objects.filter(status='completed')
        .values('requester')
        .annotate(total_claimed=Sum('food_listing__quantity'))
        .order_by('-total_claimed')[:10]
    )

    # Attach profile and badges to leaders helper
    def attach_profiles(leader_list, user_field_name, score_field_name):
        results = []
        for item in leader_list:
            user_id = item[user_field_name]
            try:
                prof = Profile.objects.get(user_id=user_id)
                results.append({
                    'profile': prof,
                    'score': item[score_field_name],
                    'badges': prof.get_badges()
                })
            except Profile.DoesNotExist:
                continue
        return results

    donors_month = attach_profiles(donor_leaderboard_month, 'donor', 'total_saved')
    receivers_month = attach_profiles(receiver_leaderboard_month, 'requester', 'total_claimed')
    donors_alltime = attach_profiles(donor_leaderboard_alltime, 'donor', 'total_saved')
    receivers_alltime = attach_profiles(receiver_leaderboard_alltime, 'requester', 'total_claimed')

    # 5. Featured Weekly Champion (Top Donor of the last 7 days)
    start_of_week = now - datetime.timedelta(days=7)
    weekly_top = (
        FoodListing.objects.filter(status='donated', created_at__gte=start_of_week)
        .values('donor')
        .annotate(total_saved=Sum('quantity'))
        .order_by('-total_saved')
        .first()
    )

    featured_champion = None
    if weekly_top:
        try:
            featured_champion = Profile.objects.get(user_id=weekly_top['donor'])
            featured_champion.weekly_score = weekly_top['total_saved']
        except Profile.DoesNotExist:
            pass

    # Fallback if no weekly donor: take top all-time donor
    if not featured_champion and donors_alltime:
        featured_champion = donors_alltime[0]['profile']
        featured_champion.weekly_score = donors_alltime[0]['score']

    context = {
        'donors_month': donors_month,
        'receivers_month': receivers_month,
        'donors_alltime': donors_alltime,
        'receivers_alltime': receivers_alltime,
        'featured_champion': featured_champion,
    }
    return render(request, 'leaderboard.html', context)


def compliance_center(request):
    return render(request, 'compliance.html')
