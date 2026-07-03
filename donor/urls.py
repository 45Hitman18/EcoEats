from django.urls import path
from . import views

app_name = 'donor'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-food/', views.add_food, name='add_food'),
    path('manage-food/', views.manage_food, name='manage_food'),
    path('bulk-manage-food/', views.bulk_manage_food, name='bulk_manage_food'),
    path('analytics/', views.donor_analytics, name='donor_analytics'),
    path('directory/', views.ngo_directory, name='ngo_directory'),
    path('csr-impact/', views.csr_impact, name='csr_impact'),
    path('driver-directory/', views.driver_directory, name='driver_directory'),
    path('allocate-food/', views.allocate_food, name='allocate_food'),
    path('broadcast-alert/', views.broadcast_alert, name='broadcast_alert'),
    path('view-requests/<int:food_id>/', views.view_requests, name='view_requests'),
    path('view-all-requests/', views.view_all_requests, name='view_all_requests'),
    path('mark-expired/<int:food_id>/', views.mark_expired, name='mark_expired'),
    path('delete-food/<int:food_id>/', views.delete_food, name='delete_food'),
    path('approve-request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('complete-request/<int:request_id>/', views.complete_request, name='complete_request'),
    path('view-feedback/', views.view_feedback, name='view_feedback'),
    path('submit-report/', views.submit_report, name='submit_report'),
    
    # Notification endpoints
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/count/', views.get_notification_count, name='get_notification_count'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
