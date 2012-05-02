# -*- coding: utf-8 -*-
from base import render
from registration.models import MysqlCreds
from ddl.forms import MySQLCreds
from registration.forms import UserForm
from django.contrib.auth.decorators import login_required
from ddl.views import utmGet


@render('404')
def error404(request):
    return {}


@login_required
@render('profile')
def profile(request):
    """
        Edit mysql creds
    """
    cred = MysqlCreds.objects.get(user=request.user)
    saved = False
    mysql_form = MySQLCreds(instance=cred)
    user_form = UserForm(instance=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        mysql_form = MySQLCreds(request.POST, instance=cred)
        _devs = utmGet("""SELECT login FROM __developers""")
        devs = []
        for dev in _devs:
            devs.append(dev['login'])
        if user_form.is_valid() and mysql_form.is_valid():
            if mysql_form.cleaned_data['db_login'] in devs:
                user_form.save()
                mysql_form.save()
                saved = True
            else:
                from django.forms.util import ErrorList
                mysql_form._errors["db_login"] = ErrorList([u"Такой логин отсутствует в таблице __developers"])
    return {'form': mysql_form, 'saved': saved, 'user_form': user_form}


# @login_required
@render('main')
def main(request):
    query = """
    SELECT *
     FROM vw_redmine_issues
     where release_date is null
     and is_accepted = 1
    """
    issues = utmGet(query)
    return {'issues': issues}
