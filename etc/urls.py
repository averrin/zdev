from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('etc.views',
    url(r'^scripts/$', 'scripts', name='scripts'),
    url(r'^merge/$', 'merge', name='merge'),
)
