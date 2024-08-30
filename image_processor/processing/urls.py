from django.urls import path
from .views import UploadCSVView, StatusView

urlpatterns = [
    path('upload/', UploadCSVView.as_view(), name='upload_csv'),
    path('status/<uuid:request_id>/', StatusView.as_view(), name='get_status'),
]
