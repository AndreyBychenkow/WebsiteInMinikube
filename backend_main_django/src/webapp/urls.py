from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    logger.info(f"Health check request received from {request.get_host()}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {request.headers}")
    return HttpResponse("OK", status=200)

urlpatterns = [
    path('', lambda request: redirect('/admin/')),
    path('admin/', admin.site.urls),
    path('health/', health_check),
]
