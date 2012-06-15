# -*- coding: utf-8 -*-
from zdev.base import render
from django.contrib.auth.decorators import login_required
from ddl.views import utmGet
# Create your views here.


@login_required
@render('etc/scripts')
def scripts(request):
    scripts = utmGet("""
        SELECT guid, item_caption, selfparent_guid FROM __script_collection order by selfparent_guid
        """)
    _scripts = {}
    for i in scripts:
        _scripts[i['guid']] = i
    scripts = {}

    for guid, item in _scripts.items():
        if not item['selfparent_guid'] or item['selfparent_guid'] is None:
            scripts[guid] = item
        else:
            parent = _scripts[item['selfparent_guid']]
            if 'childs' not in parent:
                parent['childs'] = []
            parent['childs'].append(item)

    # for script in _scripts:
    #     if not script['selfparent_guid'] or script['selfparent_guid'] is None:
    #         script['childs'] = []
    #         scripts.append(script)
    #     else:
    #         for parent in scripts:
    #             if parent['guid'] == script['selfparent_guid']:
    #                 parent['childs'].append(script)
    return {'scripts': scripts}


@render('etc/merge')
def merge(request):
    bases = utmGet('SELECT * FROM abra_bases')
    _tables = utmGet('show tables in UTM')
    tables = []
    for table in _tables:
        tables.append(table.values()[0])
    return {'bases': bases, 'tables': tables}

from ajax import *
