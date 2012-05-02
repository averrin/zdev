from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('ddl.views',
    url(r'^$', 'index', name='ddl_index'),
    # url(r'^$', 'index', name='index'),
    url(r'^edit/([\w-]*)$', 'ddl_index', name='ddl_index'),
    url(r'^save_ddl/$', 'save_ddl', name='save_ddl'),
    url(r'^list/$', 'ddl_list', name='ddl_list'),
    url(r'^odd_db/$', 'odd_db', name='odd_db'),
    url(r'^abra_bases/$', 'abra_bases', name='abra_bases'),
    url(r'^filter/$', 'filter', name='filter'),


    url(r'^modify/$', 'ddl_modify', name='modify'),
    url(r'^modify/(?P<action>[\w]*)/$', 'ddl_modify', name='modify'),
    url(r'^modify/(?P<action>[\w]*)/(?P<guid>[\w-]*)$', 'ddl_modify', name='modify'),
)
