"""uganda URL Configuration """

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
from .views import HomeView
from filebrowser.sites import site
from uganda.views import LatestInfoView

admin.autodiscover()

urlpatterns = [url(r'^$', HomeView.as_view(), name='home'),
    url(r'^admin/filebrowser/', include(site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^data/', include('acacia.data.urls',namespace='acacia')),
    url(r'^validation/', include('acacia.validation.urls',namespace='validation')),
    url(r'^accounts/', include('registration.urls')),
    
    #url(r'^info/(?P<pk>\d+)/$', latest_info, name='latest-info'),
    #url(r'^latest/(?P<pk>\d+)/$', latest_location_info, name='latest-location-info'),
    url(r'^latest/(?P<pk>\d+)/$', LatestInfoView.as_view(), name='latest-location-info'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.IMG_URL, document_root=settings.IMG_ROOT)
