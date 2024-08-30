from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.storage import default_storage
import csv
import os
import uuid
from .models import ImageProcessing
from .serializers import ImageProcessingSerializer, WebhookSerializer, ProcessedImage
from .tasks import process_images

class UploadCSVView(generics.GenericAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file part'}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith('.csv'):
            return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        file_path = os.path.join(upload_dir, file.name)
        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        request_id = uuid.uuid4()
        processing_request = ImageProcessing.objects.create(request_id=request_id)
        process_images.delay(file_path, str(request_id))
        
        serializer = ImageProcessingSerializer(processing_request)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)



class StatusView(generics.GenericAPIView):
    serializer_class = ImageProcessingSerializer

    def get(self, request, request_id, *args, **kwargs):
        try:
            processing_request = ImageProcessing.objects.get(request_id=request_id)
            serializer = self.get_serializer(processing_request)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ImageProcessing.DoesNotExist:
            return Response({'error': 'Request ID not found'}, status=status.HTTP_404_NOT_FOUND)


class WebhookView(generics.GenericAPIView):
    serializer_class = WebhookSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request_id = serializer.validated_data['request_id']
            status = serializer.validated_data['status']

            try:
                processing_request = ImageProcessing.objects.get(request_id=request_id)
                processing_request.status = status
                processing_request.save()

                # Process the images and generate the CSV
                if status == 'completed':
                    self.generate_output_csv(processing_request)
                
                return Response({'message': 'Webhook received successfully.'}, status=status.HTTP_200_OK)
            except ImageProcessing.DoesNotExist:
                return Response({'error': 'Request ID not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_output_csv(self, processing_request):
        output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file_path = os.path.join(output_dir, f'{processing_request.request_id}_output.csv')
        
        processed_images = ProcessedImage.objects.filter(request=processing_request)
        
        with open(output_file_path, 'w', newline='') as csvfile:
            fieldnames = ['Serial Number', 'Product Name', 'Input Image Urls', 'Output Image Urls']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            
            for img in processed_images:
                writer.writerow({
                    'Serial Number': img.id,
                    'Product Name': img.product_name,
                    'Input Image Urls': img.original_url,
                    'Output Image Urls': img.processed_image_path.url
                })

        processing_request.csv_file_url = default_storage.url(output_file_path)
        processing_request.save()