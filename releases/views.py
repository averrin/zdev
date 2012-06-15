# -*- coding: utf-8 -*-
from zdev.base import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
import hglib
import datetime
from ddl.views import utmGet
from zdev.settings import HG_ROOT, DOCS_FOLDERS
import os
from django.shortcuts import redirect
from registration.models import MysqlCreds
from models import Files, Pdm_sync


@render('releases/form')
@login_required
def index(request):
    """
        Form for search changed files in commits by task_num. Only render form.
        @see ajax.get_files
        @see ajax.get_branches
    """
    repos = os.walk(HG_ROOT)
    repos = repos.next()[1]
    repo = hglib.open(HG_ROOT + 'guiz')
    branches = repo.branches()
    today = datetime.date.today()
    start_date = today + datetime.timedelta(days=2 - today.weekday(), weeks=-1)
    start_date = start_date.strftime('%d.%m.%y')
    return {"branches": branches, 'start_date': start_date, 'repos': repos}


@render('releases/finish')
@login_required
def save_files(request):
    """
        Call p_add_file_to_release for list of files
    """
    _files = request.POST.items()
    files = []
    for file_name in _files:
        if not file_name[0] in ['csrfmiddlewaretoken', 'task_num', 'repo']:
            files.append(file_name)
    task_num = request.POST.get('task_num')
    repo = request.POST.get('repo')
    model = Files()
    for file_name in files:
        model.callProc('p_add_file_to_release', (task_num, file_name[0], file_name[1], repo), user=request.user)
    return {'files': files, 'task_num': task_num}


def accept_task(request, task=""):
    if task:
        utmGet("update __redmine_issues set is_accepted = 1 where redmine_id = %s" % task, commit=True)
        return responseTrue()
    else:
        responseFalse('Plz, specify task number')


def close_task(request, task=""):
    if task:
        utmGet("update __redmine_issues set release_date = now() where redmine_id = %s" % task, commit=True)
        return responseTrue()
    else:
        responseFalse('Plz, specify task number')


@render('releases/file_list')
@login_required
def files_list(request):
    """
        List of files and sql in current release
    """
    files = Files().getFiles(conditions="and redmine.is_accepted = 1")
    repos = Files().getRepos()
    users = Pdm_sync().getUsers()
    f_users = Files().getUsers()
    sql = Pdm_sync().getPdm(conditions="and ri.is_accepted = 1")
    states = utmGet('SELECT * FROM __pdm_sync_state')
    allowed_states = ['pandora', 'in_progress', 'created', 'fast_upd']
    cred = MysqlCreds.objects.get(user=request.user)
    return {'files': files, 'sql': sql,
        'repos': repos,
        'users': users,
        'states': states,
        'allowed_states': allowed_states,
        'my_name': cred.db_login,
        'f_users': f_users}


@render('releases/tasks')
@login_required
def tasks(request):
    """
        List of files and sql in tasks of current release
    """
    output = {}
    files = Files().getFiles(conditions="")
    sql = Pdm_sync().getPdm(conditions="")

    for f in files + sql:
        if not f['is_hidden']:
            if f['redmine_id'] not in output:
                output[f['redmine_id']] = {'id': f['redmine_id'],
                'subj': f['orig_ri_subj'],
                'author_name': f['author_name'],
                'assigned_name': f['assigned_name'],
                'is_accepted': f['is_accepted'],
                'files': [],
                'sql': []}
            if 'full_file_name' in f:
                f['type'] = 'file'
                output[f['redmine_id']]['files'].append(f)
            else:
                f['type'] = 'sql'
                output[f['redmine_id']]['sql'].append(f)
    output = sorted(output.items(), key=lambda x: x[1]['is_accepted'], reverse=True)

    return {'output': output}


@login_required
def file_modify(request, action, guid='', from_total=False):
    """
        Modify change from pdm_sync
        guid = change id
        action in queries dict
    """
    if guid:
        # cred = MysqlCreds.objects.get(user=request.user)
        states = utmGet('SELECT state_id,cid FROM __pdm_sync_state')
        queries = {'del': '''delete from __release_files where guid = "%s"''' % guid}
        for state in states:
            queries[state['cid']] = '''update __release_files set state_id = %s where guid = "%s"''' % (state['state_id'], guid)

        hist = utmGet('''select * from __release_files where guid = "%s"''' % guid)[0]
        if hist and action in queries:
            query = queries[action]
            utmGet(query, commit=True)
            if from_total:
                return responseTrue({'guid': guid})
            else:
                return responseTrue({'guid': guid})
        else:
            return responseFalse('File not found')
    else:
        return responseFalse('Plz, specify file guid.')


@login_required
def mass_modify(request):
    states = utmGet('SELECT state_id,cid FROM __pdm_sync_state')
    action = request.POST['action']
    guids = request.POST.getlist('guids[]')
    for guid in guids:
        queries = {'del': '''delete from __release_files where guid = "%s"''' % guid}
        for state in states:
            queries[state['cid']] = '''update __release_files set state_id = %s where guid = "%s"''' % (state['state_id'], guid)
        hist = utmGet('''select * from __release_files where guid = "%s"''' % guid)
        if hist and action in queries:
            query = queries[action]
            utmGet(query, commit=True)
    return responseTrue()


@render('releases/personal_list')
@login_required
def personal_list(request):
    """
        List of files owned by you
    """
    cred = MysqlCreds.objects.get(user=request.user)
    files = Files().getFiles(conditions="and files.developer = '%s'" % cred.db_login)
    for f in files:
        f['path_escaped'] = f['full_file_name'].replace('/', '+')
    repos = Files().getRepos()

    states = utmGet('SELECT * FROM __pdm_sync_state')
    allowed_states = ['pandora', 'in_progress', 'created', 'fast_upd']

    return {'files': files, 'repos': repos,
        'states': states,
        'allowed_states': allowed_states}


@render('releases/total_list')
@login_required
@user_passes_test(lambda u: Group.objects.get(name="task_accepters") in u.groups.all())
def total_list(request):
    """
        All files of release tasks. For review.
    """
    repos = Files().getRepos()

    f_users = Files().getUsers()

    states = utmGet('SELECT * FROM __pdm_sync_state')
    allowed_states = ['pandora', 'in_progress', 'created', 'fast_upd']
    cred = MysqlCreds.objects.get(user=request.user)
    return {
        'repos': repos,
        'states': states,
        'allowed_states': allowed_states,
        'my_name': cred.db_login,
        'f_users': f_users}


@login_required
@render('releases/total_list_inside')
def filter(request):
    q = request.POST
    conditions = ''
    if q['show_accepted'] == 'false':
        conditions += " and redmine.is_accepted = 0"
    if q['repo']:
        conditions += " and repo.rep_name = '%s'" % q['repo']
    if q['user']:
        conditions += " and d.full_name = '%s'" % q['user']
    if q['tasknum']:
        conditions += " and redmine.redmine_id = '%s'" % q['tasknum']

    states = q.getlist('states[]', [])
    for i, state in enumerate(states):
        states[i] = '"%s"' % state
    if states:
        conditions += ' and st.cid in (%s)' % ','.join(states)

    files = Files().getFiles(conditions=conditions)
    docs = DOCS_FOLDERS
    for f in files:
        if f['full_file_name'].endswith('.php') and f['repo'] in docs:
            new_file_name = os.path.basename(f['full_file_name']).replace('_', '__').replace('.', '_8')
            f['doc'] = 'http://doc.prog.zet/%s/html/%s.html' % (docs[f['repo']], new_file_name)
        f['full_name_nb'] = f['full_name'].replace(' ', '&nbsp;')
        f['path_escaped'] = f['full_file_name'].replace('/', '+')
    return {'files': files}


@login_required
@render('releases/file_view')
def file_view(request, repo, rev, path=""):
    """
        Get 'hg cat' for file rev
    """
    repo_path = repo
    repo = hglib.open(HG_ROOT + repo)
    repo.pull()
    root = repo.root()
    content = []
    if path:
        path = path.replace('+', '/')
        files = [os.path.join(root, path)]
        _content = repo.annotate(files, rev=rev, changeset=True)
        for line in _content:
            lrev = line[0]
            try:
                line = line[1].decode('cp1251')
            except:
                line = line[1]
            content.append({'badge': '<span class="label label-success">+++</span>' if lrev == rev else '', 'line': line})
    else:
        _content = repo.export([rev])
        for line in _content.split('\n'):
            badge = ''
            try:
                line = line.decode('cp1251')
            except:
                pass
            if line.startswith('+') and not line.startswith('+++'):
                badge = '<span class="label label-success">+++</span> '
                line = line[1:]
            elif line.startswith('-') and not line.startswith('---'):
                badge = '<span class="label label-important">---</span> '
                line = line[1:]
            else:
                line = '    ' + line
            content.append({'badge': badge, 'line': line})

    return {'output': content, 'repo': repo_path, 'rev': rev, 'path': path}


@login_required
@user_passes_test(lambda u: Group.objects.get(name="task_accepters") in u.groups.all())
def file_review(request):
    """
        Save file review
        @post guid
        @post text
    """
    Files().callProc('p_add_pdm_sync_comment', ('web', request.POST['guid'], request.POST['text']), user=request.user)

    return responseTrue()


@login_required
def update(request, guid=""):
    if guid:
        f = utmGet("""
            select rep_name, full_file_name from __release_files f
            join __repositories rep on (rep.rep_id = f.rep_id)
            where f.guid = '%s'
        """ % guid)[0]
        repo = hglib.open(HG_ROOT + f['rep_name'])
        repo.pull()
        file_name = '%s/%s' % (repo.root(), f['full_file_name'])
        tip = repo.log(files=[file_name])[0][1][:12]
        utmGet("""
                update __release_files set changeset_num = '%s' where guid = '%s'
            """ % (tip, guid))
        return responseTrue()
    else:
        return responseFalse('Plz, specify file guid')

from ajax import *
