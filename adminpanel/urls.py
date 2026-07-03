from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.view_users, name='view_users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/promote/', views.promote_to_admin, name='promote_to_admin'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('food-listings/', views.view_food_listings, name='view_food_listings'),
    path('reports/', views.view_reports, name='view_reports'),
    path('inquiries/', views.view_inquiries, name='view_inquiries'),
    path('export-backup/', views.export_database_backup, name='export_backup'),
    path('flush-caches/', views.flush_system_caches, name='flush_caches'),
]
