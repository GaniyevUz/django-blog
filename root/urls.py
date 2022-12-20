# from django.conf.urls import handler404
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from apps.views import InActiveView
from root import settings

admin.sites.site_header = 'My site admin header'
admin.sites.site_title = 'My site admin title'
admin.sites.index_title = 'My site admin index'

urlpatterns = [
    path('', include('apps.urls')),
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('accounts/', include('allauth.urls')),
    path('inactive/', InActiveView.as_view(), name='account_inactive'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'apps.views.entry_not_found'
