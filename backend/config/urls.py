from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from backend.config.views import index, ask, history

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', index, name='index'),
    path('ask/', ask, name='ask'),
    path('history/', history, name='history'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
