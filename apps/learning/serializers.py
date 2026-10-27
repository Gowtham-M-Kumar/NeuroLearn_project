from rest_framework import serializers
from .models import LearningProgress


class LearningProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for LearningProgress model.
    Handles reading and writing progress data.
    """
    class Meta:
        model = LearningProgress
        fields = ['id', 'module', 'item', 'completed', 'completed_at']
        read_only_fields = ['id', 'completed_at']
    
    def validate(self, data):
        """
        Ensure module and item are provided and not empty.
        """
        if not data.get('module', '').strip():
            raise serializers.ValidationError({'module': 'Module name is required.'})
        if not data.get('item', '').strip():
            raise serializers.ValidationError({'item': 'Item identifier is required.'})
        return data


class ProgressCompleteSerializer(serializers.Serializer):
    """
    Serializer for marking an item as completed.
    Used by the POST /api/learning/complete/ endpoint.
    """
    module = serializers.CharField(max_length=50, required=True)
    item = serializers.CharField(max_length=50, required=True)
    completed = serializers.BooleanField(default=True)
    
    def validate_module(self, value):
        """Ensure module name is not empty."""
        if not value.strip():
            raise serializers.ValidationError('Module name cannot be empty.')
        return value.strip()
    
    def validate_item(self, value):
        """Ensure item identifier is not empty."""
        if not value.strip():
            raise serializers.ValidationError('Item identifier cannot be empty.')
        return value.strip()
