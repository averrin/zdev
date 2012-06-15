import hglib
from subprocess import *
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from django.template.loader import render_to_string
import os
from django.http import QueryDict
from django.template import RequestContext
from zdev.base import utmGet
from zdev.settings import HG_ROOT


@dajaxice_register
def get_files(request, form):
    """
        Return Dajax json for changed files by tasknum
    """
    # form = {"task_num": "1800", "repo": "beta_building", "hide_sql": "1", "branch": "default", "csrfmiddlewaretoken": "TQ9OoZ0ciWUzqIquytVtL12eDmU4hKyq", "start_date": "01.01.12"}
    dajax = Dajax()
    form = QueryDict(form).dict()
    os.chdir(HG_ROOT + form['repo'])
    try:
        os.system('hg pull')  # i hope this unnec[c]essary
    except:
        pass
    repo = hglib.open(HG_ROOT + form['repo'])
    repo.pull()
    d, m, y = form['start_date'].split('.')
    start_date = '%s/%s/%s' % (m, d, y)
    log = repo.log(date='>%s' % start_date,
        branch=form['branch'],
        keyword='#%s' % form['task_num'])

    query = 'SELECT * FROM redmine.issues where id = %s' % form['task_num']
    task = utmGet(query, base='redmine')[0]

    files = []
    for commit in log:
        p = Popen(["hg", "log", "-M", "-r",
                commit[0],
                "--template",
                "'{node}%{files}'"],
            stdin=PIPE, stdout=PIPE)  # hglib's abilities so poor=(
        resp = p.communicate()
        if resp and resp[0]:
            rev, fs = resp[0].split('%')
            files.append({'rev': rev.strip("'")[:12], 'files': []})
            for f in fs.split(' '):
                f = f.strip("'")
                if ('hide_sql' in form and not f.endswith('.sql')) or 'hide_sql' not in form:
                    files[-1]['files'].append(f)
    file_list = {}
    for rev in files:
        for file_name in rev['files']:
            if not file_name in file_list:
                file_list[file_name] = rev['rev']
    args = {'log': log,
        'task': task,
        'files': file_list.items(),
        'task_num': form['task_num'],
        'repo': form['repo']}
    html = render_to_string('releases/list.html', args, context_instance=RequestContext(request))
    dajax.assign('#output', 'innerHTML', html)
    return dajax.json()


@dajaxice_register
def get_branches(request, repo):
    """
        Return Dajax json for branches of selected repo
    """
    dajax = Dajax()
    try:
        repo = hglib.open(HG_ROOT + repo)
        branches = repo.branches()
    except:
        branches = []
    out = ""
    if branches:
        for branch in branches:
            out += "<option value='%s'>%s</option>" % (branch[0], branch[0])
    else:
        out = '<option>---</option>'

    dajax.assign('#branch', 'innerHTML', out)
    dajax.script('$("#branch").trigger("liszt:updated")')
    return dajax.json()
