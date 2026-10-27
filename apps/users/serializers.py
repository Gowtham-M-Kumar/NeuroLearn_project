from rest_framework import serializers
from .models import ParentDevice, CustomUser, ParentProfile, ChildProfile

class ParentDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentDevice
        fields = ['fcm_token', 'device_id']

    def create(self, validated_data):
        user = self.context['request'].user
        # Update or create device token for the user
        device, created = ParentDevice.objects.update_or_create(
            user=user,
            fcm_token=validated_data['fcm_token'],
            defaults={'device_id': validated_data.get('device_id')}
        )
        return device

class ChildProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildProfile
        fields = ['id', 'user', 'age', 'learning_level', 'full_name']
        read_only_fields = ['full_name']
