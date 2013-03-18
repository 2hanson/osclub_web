from django.conf.urls.defaults import patterns, include, url

from views import *
from django.conf import settings
import os
#from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', home),
    url(r'^about$', about),
    url(r'^comment$', comment),
    url(r'^blog', include('articles.urls')),
    url(r'^ckeditor/', include('ckeditor.urls')),   

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^register/', register),
    url(r'^verify/', verify)
)
if not os.environ.has_key('OPENSHIFT_REPO_DIR'):
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_PATH,'show_indexes': True}),)

#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)        
