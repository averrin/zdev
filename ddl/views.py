# -*- coding: utf-8 -*-
""" @file
*   Main sources of DDL app. Used for work with __pdm_sync.
*
*   @author Nabrodov.A
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from zdev.base import render
from registration.models import MysqlCreds
from forms import *
from models import *
from zdev.base import *


def index(request):
    """
        Function for index page. Temporary serve ddl.html
    """
    return ddl_index(request)


@login_required
@render('ddl/ddl')
def ddl_index(request, guid=''):
    """
        Form for pdm_sync.
        If guid: check author. Open edition if author == you else open view (triggered by guid/hist/my vars)
    """
    bases = utmGet('SELECT * FROM abra_bases')
    types = utmGet('SELECT * FROM __pdm_sync_obj_types')
    kinds = utmGet('SELECT * FROM __pdm_sync_kinds')
    output = {'bases': bases, 'types': types, 'kinds': kinds}
    if guid:
        output['guid'] = guid
        cred = MysqlCreds.objects.get(user=request.user)
        hist = utmGet('''select ps.*, ri.redmine_id as task_num from vw_pdm_sync ps
            left join __redmine_issues ri on (ps.rd_id = ri.rd_id)
            where guid = "%s"''' % (guid))
        if hist:
            hist = hist[0]
            output['hist'] = hist
            output['my'] = False
            if hist['developer'] == cred.db_login:
                output['my'] = True
    return output


@login_required
@require_POST
def save_ddl(request):
    """
        Call __pdm_add_change or UPDATE if guid in request.POST
    """
    if request.method == 'GET':
        return responseFalse()
    elif request.method == 'POST':
        form = request.POST
        input_data = {
            'creds': MysqlCreds.objects.get(user=request.user),
            'db_name': form['db_name'].encode('utf8'),
            'obj_type': form['obj_type'].encode('utf8').lower(),
            'obj_name': form['obj_name'].encode('utf8').lower(),
            'hist_type': form['hist_type'].encode('utf8').lower(),
            'task_num': '' if not 'task_num' in form else form['task_num'],
            'ddl': form['ddl'],
            'comment': form['comment']
            }
        if input_data['obj_type'] == 'null':
            input_data['obj_type'] = None
        if 'guid' in form and form['guid']:
            input_data['guid'] = form['guid']
            input_data['ddl'] = input_data['ddl'].replace("'", "''")
            query = """
            UPDATE __pdm_sync set
             db_name = '%(db_name)s',
             obj_type = '%(obj_type)s',
             obj_name = '%(obj_name)s',
             ddl_body = '%(ddl)s',
             pdm_sync_kind = '%(hist_type)s',
             dev_comments = '%(comment)s'
             where guid = '%(guid)s'
            """ % (input_data)
            utmGet(query, commit=True)
        else:
            my_model().callProc('__pdm_add_change', (
                 input_data['db_name'], input_data['obj_type'], input_data['obj_name'],
                 input_data['ddl'], input_data['comment'], input_data['hist_type'], input_data['task_num']), user=request.user)
            data = {}
            for arg in input_data:
                if input_data[arg]:
                    data[arg] = "'%s'" % input_data[arg]
                else:
                    data[arg] = 'NULL'
            query = "call __pdm_add_change(%(db_name)s, %(obj_type)s, %(obj_name)s, %(ddl)s, %(comment)s)" % data
            input_data['query'] = query

        return responseTrue()


@login_required
@render('ddl/ddl_list')
def ddl_list(request):
    """
        List of changes from pdm_sync. Actually only filters list.
        @see filter
    """
    bases = utmGet('SELECT * FROM abra_bases')
    types = utmGet('SELECT * FROM __pdm_sync_obj_types')
    kinds = utmGet('SELECT * FROM __pdm_sync_kinds')
    states = utmGet('SELECT * FROM __pdm_sync_state')
    allowed_states = ['pandora', 'in_progress', 'created', 'fast_upd']
    return {'bases': bases, 'types': types, 'kinds': kinds, 'states': states, 'allowed_states': allowed_states}


@render('ddl/odd_db')
def odd_db(request):
    """
        List of databases out of abra_bases
    """
    bases = utmGet('''SELECT i.*, ab.db_name FROM information_schema.SCHEMATA i
        LEFT JOIN UTM.abra_bases ab ON (ab.db_name = i.schema_name)
        WHERE ab.db_name IS NULL''')
    return {'bases': bases}


@render('ddl/abra_bases')
def abra_bases(request):
    """
        List of databases in abra_bases
    """
    bases = utmGet("""SELECT
        db_name,
        db_desc,
        backup_file_name,
        create_time,
        db_is_absent,
        concat(developer_name,' (',developer,')') as developer_name,
        is_need_backup,
        date_actual_before as actual
        FROM vw_abra_bases ab
        order by db_name""")
    return {'bases': bases}


@render('ddl/add_db')
def add_db(request):
    """
        Add database to abra_bases
    """
    if request.method == 'GET':
        bases = utmGet('''SELECT i.*, ab.db_name FROM information_schema.SCHEMATA i
            LEFT JOIN UTM.abra_bases ab ON (ab.db_name = i.schema_name)
            WHERE ab.db_name IS NULL''')
        return {'bases': bases}
    elif request.method == 'POST':
        cred = MysqlCreds.objects.get(user=request.user)
        args = {'developer': cred.db_login, 'backup': 1 if 'backup' in request.POST else 0}
        args.update(request.POST.dict())
        query = """
            INSERT INTO abra_bases(db_name,db_desc,backup_file_name,developer,create_time,is_need_backup,date_actual_before ) VALUES(
                '%(db_name)s',
                '%(db_desc)s',
                '%(db_name)s.sql.bz2',
                '%(developer)s',
                now(),
                '%(backup)s',
                str_to_date('%(end_date)s', '%%d.%%m.%%y')
            )
        """ % args
        utmGet(query, commit=True)
        return responseTrue()


@login_required
def ddl_modify(request, action, guid=''):
    """
        Modyfi change from pdm_sync
        guid = change id
        action in queries dict

        @todo: refactor like file_modify
    """
    if guid:
        cred = MysqlCreds.objects.get(user=request.user)
        queries = {'del': '''delete from __pdm_sync where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'fast_upd': '''update __pdm_sync set state_id = 5 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'in_progress': '''update __pdm_sync set state_id = 7 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'created': '''update __pdm_sync set state_id = 1 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'pandora': '''update __pdm_sync set state_id = 6 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login)}
        hist = utmGet('''select * from __pdm_sync where guid = "%s" and developer = "%s"''' % (guid, cred.db_login))
        if hist and action in queries:
            utmGet(queries[action], commit=True)
            return responseTrue({'guid': guid})
        else:
            return responseFalse()
    else:
        return responseFalse()


@login_required
@render('ddl/list')
def filter(request):
    """
        Return rendered and filtred changes from __pdm_sync
    """
    cred = MysqlCreds.objects.get(user=request.user)
    states = request.POST.getlist('states[]', [])
    for i, state in enumerate(states):
        states[i] = '"%s"' % state
    if states:
        states = 'and cid in (%s)' % ','.join(states)
    else:
        states = ''
    db_name = request.POST.get('db_name', '')
    if db_name:
        db_name = 'and db_name = "%s"' % db_name
    obj_type = request.POST.get('obj_type', '')
    if obj_type:
        obj_type = 'and obj_type = "%s"' % obj_type
    hist_type = request.POST.get('hist_type', '')
    if hist_type:
        hist_type = 'and pdm_sync_kind = "%s"' % hist_type

    task_num = request.POST.get('task_num', '')
    if task_num:
        task_num = 'and redmine_id = "%s"' % task_num

    date_from = request.POST.get('from', '')
    if date_from:
        date_from = 'and change_time > str_to_date("%s", "%%d.%%m.%%y")' % date_from
    date_till = request.POST.get('till', '')
    if date_till:
        date_till = 'and change_time < date_add(str_to_date("%s", "%%d.%%m.%%y"), interval 1 day)' % date_till

    query = """
        SELECT ps.*, comm.c_message as review FROM vw_pdm_sync ps
            left join __pdm_sync_comments comm on (comm.ref_guid = ps.guid)
            where ps.developer = '%s'
            %s
            %s
            %s
            %s
            %s
            %s
            %s
        """ % (cred.db_login, db_name, obj_type, hist_type, task_num, date_from, date_till, states)
    history = utmGet(query)
    return {'history': history, 'query': query}
