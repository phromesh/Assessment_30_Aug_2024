from django.db import models
import uuid

class ImageProcessing(models.Model):
    request_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class ProcessedImage(models.Model):
    request = models.ForeignKey(ImageProcessing, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    original_url = models.URLField()
    processed_image_path = models.ImageField(upload_to='processed_images/')
