from django.urls import path
from .views import UploadCSVView, StatusView, WebhookView

urlpatterns = [
    path('upload/', UploadCSVView.as_view(), name='upload_csv'),
    path('status/<uuid:request_id>/', StatusView.as_view(), name='get_status'),
    path('webhook/processing_complete/', WebhookView.as_view(), name='webhook_processing_complete'),

]
