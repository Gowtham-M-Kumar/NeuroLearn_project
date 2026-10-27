from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    search_fields = ('content', 'sender__email', 'receiver__email')
