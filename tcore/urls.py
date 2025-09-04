from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.urls import path

from tcore import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quiz_finder.urls'))

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
