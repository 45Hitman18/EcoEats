from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('<int:user_id>/', views.chat, name='chat'),
    path('<int:user_id>/messages/', views.get_messages, name='get_messages'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('messages/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('<int:user_id>/read-status/', views.check_read_status, name='check_read_status'),
    path('send-location/', views.send_location_message, name='send_location'),
]
