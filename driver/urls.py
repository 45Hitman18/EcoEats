from django.urls import path
from . import views

app_name = 'driver'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('claim/<int:request_id>/', views.claim_delivery, name='claim_delivery'),
    path('update/<int:request_id>/', views.update_status, name='update_status'),
    path('accept-direct/<int:request_id>/', views.accept_direct_request, name='accept_direct_request'),
    path('decline-direct/<int:request_id>/', views.decline_direct_request, name='decline_direct_request'),
]
