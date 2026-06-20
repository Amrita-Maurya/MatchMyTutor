from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tutor/', include('peer_tutor.urls')),
    path('api/', include('peer_tutor.api.urls')),
    path('', RedirectView.as_view(url='/tutor/', permanent=False)),
]
