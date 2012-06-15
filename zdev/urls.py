from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView, RedirectView
from django.conf import settings
from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from zdev.views import *

# handler404 = 'zdev.views.error404'

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'zdev.views.home', name='home'),
    # url(r'^zdev/', include('zdev.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ddl/', include('ddl.urls')),
    url(r'^etc/', include('etc.urls')),
    url(r'^releases/', include('releases.urls')),
    url(r'^about/', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^main/$', 'zdev.views.main', name='main'),
    url(r'^$', 'zdev.views.index', name='index'),
    url(r'^help/', TemplateView.as_view(template_name='help.html'), name='help'),
    url(r'^develop/', TemplateView.as_view(template_name='develop.html'), name='develop'),
    url(r'^redirect/(?P<view_name>.*)', 'zdev.views.my_redirect', name='redirect'),

    url(r'^profile/$', 'zdev.views.profile', name='profile'),

    url(r'^go/$', 'zdev.views.go', name='go'),
    url(r'^go/(?P<page>.*)$', 'zdev.views.go', name='go'),

# account urls
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^accounts/profile/$', RedirectView.as_view(url='/')),
    url(r'^registration/', include('registration.urls')),
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),

# Temp
    # url(r'^$', 'ddl.views.index', name='index'),
    url(r'^lime/', include('lime.urls')),
)
