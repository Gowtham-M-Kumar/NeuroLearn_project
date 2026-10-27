from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import ParentDevice
from .serializers import ParentDeviceSerializer

class RegisterDeviceTokenView(generics.CreateAPIView):
    """API endpoint to save/update parent FCM device token"""
    serializer_class = ParentDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Allow both parents and children to register tokens
        return super().post(request, *args, **kwargs)
