from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('releases.views',
    url(r'^$', 'index', name='r_index'),
    # url(r'^get/$', 'get_files', name='r_get_files'),
    url(r'^list/$', 'files_list', name='r_list'),
    url(r'^save/$', 'save_files', name='r_save'),
)
