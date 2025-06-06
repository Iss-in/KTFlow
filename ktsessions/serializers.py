from rest_framework import serializers
from .models import KTSession, Attachment


class KTSessionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = KTSession
        fields = ('id', 'title', 'description', 'created_by', 'created_by_name',
                  'share_token', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'created_by_name')


class KTSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KTSession
        fields = ('title', 'description')

    def create(self, validated_data):
        # Set the created_by to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class KTSessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KTSession
        fields = ('title', 'description')


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['file_type', 'file_url', 'summary', 'transcript']

class SessionPublicSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = KTSession
        fields = ['title', 'description', 'attachments']
