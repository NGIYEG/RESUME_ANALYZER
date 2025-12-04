from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Companyapp.urls')),
    path('review_dashboard/', include('Analyzerapp.urls')),
    path('application/', include('Applicantapp.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django browser reload (dev only)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]