from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import Message
from .forms import MessageForm
from accounts.models import User
import datetime

def get_chat_users_with_previews(current_user):
    users = User.objects.exclude(id=current_user.id)
    chat_users = []
    
    for u in users:
        # Get last message
        last_msg = Message.objects.filter(
            (Q(sender=current_user) & Q(receiver=u)) |
            (Q(sender=u) & Q(receiver=current_user))
        ).order_by('-timestamp').first()
        
        # Get unread count sent by this contact
        unread_count = Message.objects.filter(
            sender=u,
            receiver=current_user,
            is_read=False
        ).count()
        
        preview = ""
        last_time = None
        if last_msg:
            if last_msg.content:
                preview = last_msg.content
            elif last_msg.file:
                preview = "📎 Attachment"
            last_time = last_msg.timestamp
            
        chat_users.append({
            'user': u,
            'role_display': u.profile.get_role_display() if hasattr(u, 'profile') else "Partner",
            'last_message': preview,
            'last_time': last_time,
            'unread_count': unread_count,
        })
        
    # Sort by last message time (most recent first)
    chat_users.sort(key=lambda x: x['last_time'] if x['last_time'] else timezone.make_aware(datetime.datetime.min), reverse=True)
    return chat_users

@login_required
def chat_list(request):
    chat_users = get_chat_users_with_previews(request.user)
    
    dashboard_url = '/'
    if hasattr(request.user, 'profile'):
        if request.user.profile.role == 'donor':
            dashboard_url = '/donor/dashboard/'
        elif request.user.profile.role == 'receiver':
            dashboard_url = '/receiver/dashboard/'
        elif request.user.profile.role == 'driver':
            dashboard_url = '/driver/dashboard/'
        elif request.user.profile.role == 'admin':
            dashboard_url = '/adminpanel/'
            
    return render(request, 'chat/chat_list.html', {
        'chat_users': chat_users,
        'dashboard_url': dashboard_url
    })

@login_required
def chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Mark messages from other_user to request.user as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    chat_users = get_chat_users_with_previews(request.user)
    
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            return redirect('chat:chat', user_id=user_id)
    else:
        form = MessageForm()

    dashboard_url = '/'
    if hasattr(request.user, 'profile'):
        if request.user.profile.role == 'donor':
            dashboard_url = '/donor/dashboard/'
        elif request.user.profile.role == 'receiver':
            dashboard_url = '/receiver/dashboard/'
        elif request.user.profile.role == 'driver':
            dashboard_url = '/driver/dashboard/'
        elif request.user.profile.role == 'admin':
            dashboard_url = '/adminpanel/'

    return render(request, 'chat/chat.html', {
        'other_user': other_user,
        'messages': messages,
        'current_user': request.user,
        'form': form,
        'chat_users': chat_users,
        'dashboard_url': dashboard_url
    })

@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    last_message_id = request.GET.get('last_message_id', 0)

    # Fetch new messages
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).filter(id__gt=last_message_id).order_by('timestamp')

    # Mark new incoming messages as read
    messages.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    messages_data = []
    for message in messages:
        message_data = {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%I:%M %p'),
            'is_sent': message.sender == request.user,
            'is_read': message.is_read,
        }
        if message.file:
            message_data['file_url'] = message.file.url
            message_data['file_name'] = message.file.name.split('/')[-1]
        messages_data.append(message_data)

    return JsonResponse({'messages': messages_data})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.sender != request.user:
        return JsonResponse({'error': 'You can only delete your own messages'}, status=403)
    message.delete()
    return JsonResponse({'success': True})

@login_required
def check_read_status(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    # Return IDs of all read messages sent by current user to this contact
    read_message_ids = list(
        Message.objects.filter(sender=request.user, receiver=other_user, is_read=True)
        .values_list('id', flat=True)
    )
    return JsonResponse({'read_message_ids': read_message_ids})

@login_required
def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.sender != request.user:
        return JsonResponse({'error': 'You can only edit your own messages'}, status=403)

    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            new_content = data.get('content', '').strip()
            if new_content:
                message.content = new_content
                message.save()
                return JsonResponse({'success': True, 'content': new_content})
            else:
                return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def send_location_message(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        donor_id = data.get('donor_id')
        receiver_id = data.get('receiver_id')
        lat = data.get('latitude')
        lng = data.get('longitude')

        if not lat or not lng:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)

        from django.contrib.auth.models import User
        from .models import Message

        # Create Google Maps tracking link
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        msg_text = f"📍 Driver Live Location: I am currently en route. Track my location on Google Maps: {maps_link}"

        messages_sent = 0
        if donor_id:
            try:
                donor_user = User.objects.get(id=donor_id)
                Message.objects.create(
                    sender=request.user,
                    receiver=donor_user,
                    content=msg_text
                )
                messages_sent += 1
            except User.DoesNotExist:
                pass

        if receiver_id:
            try:
                receiver_user = User.objects.get(id=receiver_id)
                Message.objects.create(
                    sender=request.user,
                    receiver=receiver_user,
                    content=msg_text
                )
                messages_sent += 1
            except User.DoesNotExist:
                pass

        return JsonResponse({'success': True, 'messages_sent': messages_sent})
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)


import time
import json
from django.http import StreamingHttpResponse
from donor.models import Notification

@login_required
def chat_stream(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    def event_stream():
        last_id = 0
        yield f"data: {json.dumps({'connected': True})}\n\n"
        while True:
            new_msgs = Message.objects.filter(
                (Q(sender=request.user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=request.user))
            ).filter(id__gt=last_id).order_by('timestamp')
            
            if new_msgs.exists():
                for msg in new_msgs:
                    last_id = max(last_id, msg.id)
                    # Mark incoming messages as read
                    if msg.sender == other_user and not msg.is_read:
                        msg.is_read = True
                        msg.save(update_fields=['is_read'])
                    
                    data = {
                        'id': msg.id,
                        'content': msg.content,
                        'timestamp': msg.timestamp.strftime('%I:%M %p'),
                        'is_sent': msg.sender == request.user,
                        'is_read': msg.is_read,
                    }
                    if msg.file:
                        data['file_url'] = msg.file.url
                        data['file_name'] = msg.file.name.split('/')[-1]
                    yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
            
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def notification_stream(request):
    def event_stream():
        last_id = 0
        yield f"data: {json.dumps({'connected': True})}\n\n"
        while True:
            new_notifications = Notification.objects.filter(
                recipient=request.user,
                id__gt=last_id
            ).order_by('created_at')
            
            if new_notifications.exists():
                for notif in new_notifications:
                    last_id = max(last_id, notif.id)
                    data = {
                        'id': notif.id,
                        'title': notif.title,
                        'message': notif.message,
                        'type': notif.notification_type,
                        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)
            
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

