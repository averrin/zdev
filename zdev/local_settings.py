import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zdev',
        'USER': 'averrin',
        'PASSWORD': 'aqwersdf',
        'HOST': 'dev-hg.zet',
        'PORT': '',
    }
}

PROJECT_PATH = os.path.expanduser('/home/alexey.a.nabrodov//Dropbox/django_projects/zdev/')
