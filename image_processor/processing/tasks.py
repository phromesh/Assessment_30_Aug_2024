from celery import shared_task
from PIL import Image
from io import BytesIO
import pandas as pd
import requests
import os
from .models import ImageProcessing, ProcessedImage

@shared_task
def process_images(file_path, request_id):
    processing_request = ImageProcessing.objects.get(request_id=request_id)
    processing_request.status = 'processing'
    processing_request.save()

    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        product_name = row['Product Name']
        urls = row['Input Image Urls'].split(',')
        output_urls = row['Output Image Urls'].split(',')
        
        for url, output_url in zip(urls, output_urls):
            response = requests.get(url.strip())
            image = Image.open(BytesIO(response.content))
            image = image.resize((int(image.width * 0.5), int(image.height * 0.5)))
            
            output_image_path = os.path.join('media/processed_images', os.path.basename(output_url))
            image.save(output_image_path)
            
            ProcessedImage.objects.create(
                request_id=processing_request,
                product_name=product_name,
                original_url=url.strip(),
                processed_image_path=output_image_path
            )

    processing_request.status = 'completed'
    processing_request.save()
