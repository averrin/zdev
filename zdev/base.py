from django.shortcuts import render_to_response
from django.template import RequestContext
from zdev.settings import JS_DEBUG
from django.contrib.auth.models import Group
from functools import partial
from registration.models import MysqlCreds
import MySQLdb
from zdev.settings import UTM_HOST, UTM_NAME
from django.db import connection

from itertools import *
import json
from django.http import HttpResponse


def responseTrue(args=""):
    response = {'success': True}
    if args:
        response.update(args)
    return HttpResponse(json.dumps(response))


def responseFalse(exception=""):
    raise Exception(exception)


def connectUTM(user, anonimous=False, base=""):
    """
        return connection for UTM base
    """
    if not anonimous:
        user_db = MysqlCreds.objects.get(user=user)
        db = MySQLdb.connect(host=UTM_HOST,
                     user=user_db.db_login,
                     passwd=user_db.db_password,
                     db=base if base else UTM_NAME,
                     charset='cp1251')
    else:
        db = connection
    return db


def utmGet(query, user="", commit=False, base=""):
    """
        Execute query and return results
    """
    query = query.replace('%', '%%')
    db = connectUTM(user, False if user else True, base if base else UTM_NAME)
    cursor = db.cursor()
    cursor.execute(query)
    if commit:
        try:
            db.commit()
        except:
            pass
    _result = cursor.fetchall()
    if cursor.description is not None and len(cursor.description) > 0:
        col_names = [desc[0] for desc in cursor.description]
    # while True:
    #     row = cursor.fetchone()
    #     if row is None:
    #         break
    #     row_dict = dict(izip(col_names, row))
    #     yield row_dict
    # raise Exception(row_dict)
        result = []
        for row in _result:
            result.append(dict(izip(col_names, row)))
    else:
        result = _result
    return result


def render(template):
    def renderer(func):
        def wrapper(request, *args, **kw):
            output = func(request, *args, **kw)
            if isinstance(output, (list, tuple)):
                return render_to_response(
                    output[1], output[0], RequestContext(request))
            elif isinstance(output, dict):
                return render_to_response(
                    '%s.html' % template, output, RequestContext(request))
            return output
        return wrapper
    return renderer


def my_context(request):
    """
        My context processor
    """
    is_task_accepter = Group.objects.get(name="task_accepters") in request.user.groups.all()
    return {'JS_DEBUG': str(JS_DEBUG).lower(), 'is_task_accepter': is_task_accepter}


class my_model(object):
    """
        pseudo-model for UTM
    """
    def __init__(self):
        self._createProcs()

    def _createProcs(self):
        """
            Create functions for execute queryes
        """
        d = self.__dict__.copy()
        for q in d:
            query = self.__dict__[q]
            self.__setattr__(q[1:],
                partial(self.execQuery, q=query))

    def execQuery(self, q, *args, **kwargs):
        """
            Format query and execute
        """
        query = q % kwargs
        return utmGet(query)

    def callProc(self, proc_name, args, user=''):
        """
            Call procedure
        """
        db = connectUTM(user, False if user else True)
        cursor = db.cursor()
        cursor.callproc(proc_name, args)
        db.commit()
