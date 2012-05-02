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
import MySQLdb
from zdev.settings import UTM_HOST, UTM_NAME


def connectUTM(user, anonimous=False):
    """
        return connection for UTM base
    """
    if not anonimous:
        user_db = MysqlCreds.objects.get(user=user)
        db = MySQLdb.connect(host=UTM_HOST,
                     user=user_db.db_login,
                     passwd=user_db.db_password,
                     db=UTM_NAME,
                     charset='cp1251')
    else:
        db = MySQLdb.connect(host=UTM_HOST,
                     user='vmironov',
                     passwd='qq2',
                     db=UTM_NAME,
                     charset='cp1251')

    return db


def utmGet(query, user=""):
    """
        Execute query and return results
    """
    db = connectUTM(user, False if user else True)
    cursor = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    return cursor.fetchall()


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
@render('ddl/finish')
def save_ddl(request):
    """
        Call __pdm_add_change or UPDATE if guid in request.POST
    """
    if request.method == 'GET':
        return redirect(index)
    elif request.method == 'POST':
        form = request.POST
        db = connectUTM(request.user)
        input_data = {
            'creds': MysqlCreds.objects.get(user=request.user),
            'db_name': form['db_name'].encode('utf8'),
            'obj_type': form['obj_type'].encode('utf8').lower(),
            'obj_name': form['obj_name'].encode('utf8').lower(),
            'hist_type': form['hist_type'].encode('utf8').lower(),
            'task_num': form['task_num'],
            'ddl': form['ddl'].replace("'", '"'),
            'comment': form['comment'].replace("'", '"')
            }
        cursor = db.cursor()
        if input_data['obj_type'] == 'null':
            input_data['obj_type'] = None
        if 'guid' in form and form['guid']:
            input_data['guid'] = form['guid']
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
            cursor.execute(query)
            db.commit()
        else:
            cursor.callproc('__pdm_add_change', (
                 input_data['db_name'], input_data['obj_type'], input_data['obj_name'],
                 input_data['ddl'], input_data['comment'], input_data['hist_type'], input_data['task_num']))
            cursor.close()
            db.commit()
            data = {}
            for arg in input_data:
                if input_data[arg]:
                    data[arg] = "'%s'" % input_data[arg]
                else:
                    data[arg] = 'NULL'

            query = "call __pdm_add_change(%(db_name)s, %(obj_type)s, %(obj_name)s, %(ddl)s, %(comment)s)" % data
            input_data['query'] = query

        return input_data


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
    allowed_states = ['pandora', 'tmp_rec', 'created', 'fast_upd']
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
        is_need_backup
        FROM vw_abra_bases ab
        order by db_name""")
    return {'bases': bases}


@login_required
@render('ddl/ddl_modify')
def ddl_modify(request, action, guid=''):
    """
        Modyfi change from pdm_sync
        guid = change id
        action in queries dict
    """
    if guid:
        cred = MysqlCreds.objects.get(user=request.user)
        db = connectUTM(request.user)
        queries = {'del': '''delete from __pdm_sync where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'fast_upd': '''update __pdm_sync set state_id = 5 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'tmp_rec': '''update __pdm_sync set state_id = 4 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'created': '''update __pdm_sync set state_id = 1 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login),
        'pandora': '''update __pdm_sync set state_id = 6 where guid = "%s" and developer = "%s"''' % (guid, cred.db_login)}
        cursor = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute('''select * from __pdm_sync where guid = "%s" and developer = "%s"''' % (guid, cred.db_login))
        hist = cursor.fetchone()
        if hist and action in queries:
            cursor.execute(queries[action])
            db.commit()
            success = True
            return redirect(ddl_list)
        else:
            success = False
        return {'success': success, 'guid': guid}
    else:
        return redirect(ddl_list)


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

    query = """SELECT * FROM
        vw_pdm_sync ps
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
