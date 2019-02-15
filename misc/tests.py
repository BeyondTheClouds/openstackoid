from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneauth1.adapter import Adapter
from keystoneclient.v3 import client

# URL = '10.0.2.15'
URL = '192.168.141.245:8888'

# ipdb> vars(auth1)
# {'_username': 'glance', '_user_domain_name': 'Default', 'auth_ref': None,
#  '_discovery_cache': {}, '_domain_id': None, '_user_domain_id': None,
#  'auth_url': 'http://192.168.141.245:8888/identity', '_password': 'admin',
#  '_domain_name': None, '_default_domain_name': None, '_trust_id': None,
#  '_plugin': <keystoneauth1.identity.v3.password.Password object at
#  0x7fd460b8ab90>, '_project_domain_name': 'Default', 'reauthenticate': True,
#  '_system_scope': None, '_lock': <thread.lock object at 0x7fd45f5ab5f0>,
#  '_project_name': 'service', '_default_domain_id': None, '_project_id': None,
#  '_project_domain_id': None, '_user_id': None}
# ipdb> vars(auth1._plugin)
# {'project_name': 'service', 'unscoped': False, 'reauthenticate': True,
#  '_discovery_cache': {}, '_lock': <thread.lock object at 0x7fd45e468430>,
#  'auth_ref': None, 'domain_name': None, 'system_scope': None, 'auth_methods':
#  [<keystoneauth1.identity.v3.password.PasswordMethod object at 0x7fd45e113710>],
#  'auth_url': u'http://10.0.2.15/identity/v3/', 'project_domain_name': 'Default',
#  'include_catalog': True, 'project_id': None, 'domain_id': None, 'trust_id':
#  None, 'project_domain_id': None}
# ipdb> vars(auth1._plugin.auth_methods[0])
# {'username': 'glance', 'user_domain_name': 'Default', 'password': 'admin',
#  'user_id': None, 'user_domain_id': None}
#
# Note: It works if I do a,
# auth = copy.copy(self._auth)
# auth.auth_url = auth_url
# auth._plugin.auth_url = auth_url + '/v3'
# sess = Session(auth=auth)


auth = v3.Password(
    # auth_url="http://%s/identity/v3" % URL,
    auth_url="http://192.168.141.245:8888/identity/v3",
    username='glance',
    password='admin',
    project_domain_name='Default',
    user_domain_name='Default',
    # domain_id=None,
    user_domain_id=None,
    # default_domain_name=None,
    # default_domain_id=None,
    # project_id=None,
    # project_domain_id=None,
    user_id=None,
    # trust_id=None,
    # system_scope=None,
    project_name='service',
    reauthenticate=True,
    include_catalog=True)

print(vars(auth))
sess = Session(auth=auth)

# print(sess.get("http://%s/identity/v3" % URL))
print("Auth Token: %s" % auth.get_auth_ref(sess).auth_token)
print(sess.get_endpoint(service_type='identity'))

# adapter = Adapter(
#     session=sess,
#     service_type='identity',
#     interface='admin')

# print(adapter.get('users'))



# ks = client.Client(session=sess)
# users = ks.users.list()

            # _auth.get_auth_ref(_session) # should get a token
            # _session.get_endpoint(service_type='identity')

# auth = v3.Password(auth_url='http://%s:5000/v3' % keystone_addr,
#                        username='admin',
#                        password='demo',
#                        project_name='admin',
#                        user_domain_id='default',
#                    project_domain_id='default')
