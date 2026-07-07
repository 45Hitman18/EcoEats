from django.urls import path

from . import views

app_name = 'receiver'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('route-map/', views.route_map, name='route_map'),
    path('batch-claim/', views.batch_claim, name='batch_claim'),
    path('driver-directory/', views.driver_directory, name='driver_directory'),
    path('food/<int:food_id>/', views.food_detail, name='food_detail'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('submit-report/', views.submit_report, name='submit_report'),
    path('live-drivers/', views.live_drivers, name='live_drivers'),
    
    # Notification endpoints
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/count/', views.get_notification_count, name='get_notification_count'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
