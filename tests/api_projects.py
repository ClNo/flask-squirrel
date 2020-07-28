from tests.api_tools import ApiClient
from tests.client_app_config import client_config


class ProjectsData(ApiClient):
    project1 = {
        'name': 'Proj ABC 2019-10 A', 'comment': 'Comment 2019', 'project_state': 'running',
        'date_started': '2019-09-04', 'date_finished': None
    }
    project2 = {
        'name': 'Proj DEF 2020-11 B', 'project_state': 'running',
        'date_started': '2020-01-04'
    }
    project3 = {
        'name': 'Proj XYZ 2015-01 X', 'project_state': 'finished',
        'date_started': '2015-01-04', 'date_finished': '2018-03-05'
    }

    def __init__(self):
        ApiClient.__init__(self, 'projects')
        self.db_spec = client_config.db_spec
        self.id_project1 = None
        self.id_project2 = None
        self.id_project3 = None

    def initial_data(self):
        self.query_size(0)
        self.login_admin()  # assertion if failed
        self._create_tests()
        self.query_size(3)

    def _create_tests(self):
        reply = self.api_create_entry(0, self.project1)
        self.check_reply(reply, self.project1)
        self.id_project1 = self.get_primary_id(reply, self.db_spec)

        reply = self.api_create_entry(0, self.project2)
        self.check_reply(reply, self.project2)
        self.id_project2 = self.get_primary_id(reply, self.db_spec)

        assert self.id_project2 == (self.id_project1 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_project1, self.id_project2)

        reply = self.api_create_entry(0, self.project3)
        self.check_reply(reply, self.project3)
        self.id_project3 = self.get_primary_id(reply, self.db_spec)

        assert self.id_project3 == (self.id_project2 + 1),\
            'primary key of {0} not auto incrementing (id2:{1} id3:{2})'.format(self.resource_name, self.id_project2, self.id_project3)


proj_api = ProjectsData()
