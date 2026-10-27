from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Message
from apps.users.models import CustomUser, ChildProfile
import json

@login_required
def message_dashboard(request):
    """View to list all possible contacts"""
    user = request.user
    
    # Show only valid roles (Teacher and Child) as contacts
    contacts = CustomUser.objects.filter(
        role__in=[CustomUser.UserRole.TEACHER, CustomUser.UserRole.CHILD]
    ).exclude(id=user.id).order_by('-last_login')
        
    return render(request, 'messaging/dashboard.html', {'contacts': contacts})

@login_required
def chat_detail(request, user_id):
    """View to see messages with a specific user"""
    other_user = get_object_or_404(CustomUser, id=user_id)
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # Mark messages as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'messaging/chat.html', {
        'other_user': other_user,
        'messages': messages
    })

@login_required
def send_message_ajax(request):
    """API view to send a message via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receiver_id = data.get('receiver_id')
            content = data.get('content')
            
            if not receiver_id or not content:
                return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
                
            receiver = CustomUser.objects.get(id=receiver_id)
            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content
            )
            
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'sender_id': message.sender.id
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@login_required
def get_new_messages_ajax(request, other_user_id):
    """API view for AJAX polling to get new messages"""
    last_id = request.GET.get('last_id', 0)
    other_user = get_object_or_404(CustomUser, id=other_user_id)
    
    new_messages = Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        id__gt=last_id
    ).order_by('timestamp')
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name()
        })
        msg.is_read = True
        msg.save()
        
    return JsonResponse({'messages': messages_data})
