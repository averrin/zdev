from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('releases.views',
    url(r'^$', 'index', name='files.send'),
    # url(r'^get/$', 'get_files', name='r_get_files'),
    url(r'^list/$', 'files_list', name='release_files'),
    url(r'^personal_list/$', 'personal_list', name='files.personal_list'),
    url(r'^total_list/$', 'total_list', name='files.total_list'),
    url(r'^filter/$', 'filter', name='files.filter'),
    url(r'^tasks/$', 'tasks', name='tasks'),
    url(r'^save/$', 'save_files', name='files_save'),
    url(r'^accept_task/$', 'accept_task', name='accept_task'),
    url(r'^accept_task/(?P<task>[\d]+)$', 'accept_task', name='accept_task'),
    url(r'^close_task/$', 'close_task', name='close_task'),
    url(r'^close_task/(?P<task>[\d]+)$', 'close_task', name='close_task'),

    url(r'^modify/$', 'file_modify', name='file_modify'),
    url(r'^mass_modify/$', 'mass_modify', name='mass_modify'),
    url(r'^modify/(?P<action>[\w]*)/$', 'file_modify', name='file_modify'),
    url(r'^modify/(?P<action>[\w]*)/(?P<guid>[\w-]*)$', 'file_modify', name='file_modify'),
    url(r'^update/$', 'update', name='file_update'),
    url(r'^update/(?P<guid>[\w-]*)$', 'update', name='file_update'),
    url(r'^modify/t/$', 'file_modify', name='file_modify_t', kwargs={'from_total': True}),
    url(r'^modify/t/(?P<action>[\w]*)/(?P<guid>[\w-]*)$', 'file_modify', name='file_modify_t', kwargs={'from_total': True}),

    url(r'^view/(?P<repo>[\w-]*)/(?P<rev>[\w]*)/(?P<path>.*)$', 'file_view', name='file_view'),
    url(r'^view/(?P<repo>[\w-]*)/(?P<rev>[\w]*)', 'file_view', name='file_view'),
    url(r'^review/$', 'file_review', name='file_review'),
    url(r'^get_files/(?P<form>.*)$', 'get_files', name='get_files'),

)
