# -*- coding: utf-8 -*-
from zdev.base import render
from django.contrib.auth.decorators import login_required
import hglib
import datetime
from ddl.views import connectUTM, utmGet
from zdev.settings import HG_ROOT
import os


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
    db = connectUTM(request.user)
    cursor = db.cursor()
    for file_name in files:
        cursor.callproc('p_add_file_to_release2', (task_num, file_name[0], file_name[1], repo))
    db.commit()
    return {'files': files, 'task_num': task_num}


@render('releases/file_list')
@login_required
def files_list(request):
    """
        List of files and sql in current release
    """
    query = """
    SELECT files.*, repo.rep_name as repo, redmine.* FROM __release_files files
     left join vw_redmine_issues redmine on (files.rd_id = redmine.rd_id)
     left join __repositories repo on (files.rep_id = repo.rep_id)
     where redmine.release_date is null
    """
    files = utmGet(query)

    query = """
    SELECT repo.rep_name
     from __release_files files
     left join __repositories repo on (files.rep_id = repo.rep_id)
     group by files.rep_id
    """
    repos = utmGet(query)

    query = """
    SELECT
     concat(d.full_name,' (',d.login,')') as developer
    FROM
     vw_pdm_sync vps
    left join __vw_developers d on (d.login = vps.developer)
    where vps.install_serv_time is null
    and vps.state_id in (3,2) group by d.login
    """
    users = utmGet(query)

    query = """
    SELECT
     vps.obj_type, vps.obj_name,
     vps.ddl_body_200,
     vps.dev_comments, ri.redmine_id,
     vps.state_name,
     ris.subject as redmine_subject,
     concat(d.full_name,' (',d.login,')') as developer,
     vps.cid
    FROM
     vw_pdm_sync vps
    join __redmine_issues ri on (ri.rd_id = vps.rd_id)
    left join redmine.issues ris on (ris.id = ri.redmine_id)
    left join __vw_developers d on (d.login = vps.developer)
    where vps.install_serv_time is null
    and ri.release_date is null
    and vps.state_id in (3,2)
    """
    sql = utmGet(query)
    return {'files': files, 'sql': sql, 'repos': repos, 'users': users}

from ajax import *
