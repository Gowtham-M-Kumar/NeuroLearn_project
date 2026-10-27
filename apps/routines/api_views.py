from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import ChildRoutine
from .serializers import ChildRoutineSerializer

class ChildRoutineViewSet(viewsets.ModelViewSet):
    """API endpoint to create/update child routines. Restricted to child's parent."""
    serializer_class = ChildRoutineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'parent':
            # Get routines for all children assigned to this parent
            return ChildRoutine.objects.filter(child__child_profile__parents__user=user)
        elif user.role == 'child':
            return ChildRoutine.objects.filter(child=user)
        return ChildRoutine.objects.none()

    def perform_create(self, serializer):
        serializer.save()
