from rest_framework import serializers
from .models import ChildRoutine

class ChildRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildRoutine
        fields = ['id', 'child', 'title', 'time', 'repeat_days', 'notify_parent', 'is_active']
        read_only_fields = ['id']

    def validate_child(self, value):
        # Ensure the child belongs to the requesting parent
        user = self.context['request'].user
        if user.role != 'parent':
            raise serializers.ValidationError("Only parents can manage routines.")
        
        if not value.child_profile.parents.filter(user=user).exists():
            raise serializers.ValidationError("This child is not assigned to you.")
        return value
