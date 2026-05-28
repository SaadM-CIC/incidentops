from apps.dashboard.views import DashboardRedirectView
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('comments/', include('apps.comments.urls')),
    path('notifications/', include('apps.notifications.urls')), 
    path('dashboard/', include('apps.dashboard.urls')),  
    path('', DashboardRedirectView.as_view(), name='home'),
    path('ai/', include('apps.ai_classifier.urls')),
    path('', TemplateView.as_view(template_name='public/home.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
