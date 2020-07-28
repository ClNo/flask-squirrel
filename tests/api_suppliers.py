from tests.api_tools import ApiClient
from tests.client_app_config import client_config


class SuppliersData(ApiClient):
    supplier1 = {
        'name': 'Max Supplier'
    }
    supplier2 = {
        'name': 'Supplier 123 456'
    }

    def __init__(self):
        ApiClient.__init__(self, 'suppliers')
        self.db_spec = client_config.db_spec
        self.id_supplier1 = None
        self.id_supplier2 = None

    def initial_data(self):
        self.query_size(0)
        self.login_admin()  # assertion if failed
        self._create_tests()
        self.query_size(2)

    def _create_tests(self):
        reply = self.api_create_entry(0, self.supplier1)
        self.check_reply(reply, self.supplier1)
        self.id_supplier1 = self.get_primary_id(reply, self.db_spec)

        reply = self.api_create_entry(0, self.supplier2)
        self.check_reply(reply, self.supplier2)
        self.id_supplier2 = self.get_primary_id(reply, self.db_spec)

        assert self.id_supplier2 == (self.id_supplier1 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_supplier1, self.id_supplier2)


suppl_api = SuppliersData()
