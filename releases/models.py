from django.db import models
from zdev.base import my_model


class Files(my_model):
    """
        @see zdev.base.my_model
    """
    def __init__(self):
        self._getFiles = """
            SELECT files.*, repo.rep_name as repo, redmine.* ,st.state_name, st.cid, d.full_name, c.c_message as review
                FROM __release_files files
                    left join vw_redmine_issues redmine on (files.rd_id = redmine.rd_id)
                    left join __repositories repo on (files.rep_id = repo.rep_id)
                    left join __pdm_sync_state st on (st.state_id = files.state_id)
                    left join __vw_developers d on (d.login = files.developer)
                    left join __pdm_sync_comments c on (c.ref_guid = files.guid)
                where redmine.release_date is null
                    %(conditions)s
                group by guid order by st.priority desc
        """
        self._getRepos = """
            SELECT repo.rep_name
                from __release_files files
                    left join __repositories repo on (files.rep_id = repo.rep_id)
                group by files.rep_id
            """

        self._getUsers = """
            SELECT d.full_name
                FROM __release_files files
                    left join vw_redmine_issues redmine on (files.rd_id = redmine.rd_id)
                    left join __vw_developers d on (d.login = files.developer)
                where redmine.release_date is null
                group by d.full_name
            """
        my_model.__init__(self)


class Pdm_sync(my_model):
    """
        @see zdev.base.my_model
    """
    def __init__(self):
        self._getPdm = """
            SELECT ri.*, ps.*
                FROM
                    vw_redmine_issues ri
                    join vw_pdm_sync ps on (ri.rd_id = ps.rd_id)
                where ri.release_date is null
                %(conditions)s
            """

        self._getUsers = """
            SELECT concat(ri.assigned_name, ' (', ps.developer, ')') as developer
                FROM
                    vw_redmine_issues ri
                    join vw_pdm_sync ps on (ri.rd_id = ps.rd_id)
                where ri.release_date is null and ri.is_accepted = 1 group by ps.developer
            """

        my_model.__init__(self)
