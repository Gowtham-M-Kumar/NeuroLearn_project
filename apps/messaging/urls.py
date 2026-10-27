from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.message_dashboard, name='dashboard'),
    path('chat/<int:user_id>/', views.chat_detail, name='chat_detail'),
    path('api/send/', views.send_message_ajax, name='send_message_ajax'),
    path('api/poll/<int:other_user_id>/', views.get_new_messages_ajax, name='get_new_messages_ajax'),
]
