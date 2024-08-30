from rest_framework import serializers
from .models import ImageProcessing, ProcessedImage

class ImageProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProcessing
        fields = ['request_id', 'status']

class ProcessedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedImage
        fields = ['product_name', 'original_url', 'processed_image_path']

class WebhookSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['completed', 'failed'])
