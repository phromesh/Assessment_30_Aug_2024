from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.storage import default_storage
import os
import uuid
from .models import ImageProcessing
from .serializers import ImageProcessingSerializer
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
