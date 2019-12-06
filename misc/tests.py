import logging

from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneauth1.adapter import Adapter
from keystoneclient.v3 import client

logger = logging.getLogger('keystoneauth')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

OS = { 'url': '192.168.141.245:8888', 'name': 'CloudOne' }
# OS = { 'url': '192.168.142.245:8888', 'name': 'CloudTwo' }

# import ipdb; ipdb.set_trace()
auth = v3.Password(
        # Use Admin credential -- Same everywhere in this PoC!
        project_domain_id='default',
        user_domain_id='default',
        username='admin',
        password='admin',
        # The `plugin_creator` of `_create_auth_plugin` automatically add the
        # V3, but here we have to manually add it.
        auth_url="http://%s/identity/v3" % OS['url'],
        # Allow fetching a new token if the current one is going to expire
        reauthenticate=True,
        # Project scoping is mandatory to get the service catalog fill properly.
        project_name='admin',    # for project's scoping
        include_catalog=True,    # include the service catalog in the token
    )

print(vars(auth))
sess = Session(auth=auth)

print("no auth_ref (token) %s" % auth.auth_ref)

# import ipdb; ipdb.set_trace()

# print(sess.get("http://%s/identity/v3" % OS['url']))
# Authenticate
auth.get_access(sess)
auth_ref = auth.auth_ref
print("Auth Token: %s" % auth_ref.auth_token)

import ipdb; ipdb.set_trace()

# Service catalog
print("Has service catalog: %s" % auth_ref.has_service_catalog())
print("Service catalog: %s" % auth_ref.service_catalog.catalog)

print(sess.get_endpoint(service_type='identity'))

# import ipdb; ipdb.set_trace()
ks_adap = Adapter(
    auth=auth,
    session=sess,
    service_type='identity',
    interface='admin',
    region_name=OS['name'])

services = ks_adap.get('/v3/services')
print(services.json())


# Discover net
net_adap = Adapter(
    auth=auth,
    session=sess,
    service_type='network',
    interface=['internal', 'public'],
    region_name=OS['name'])

net_discovery = net_adap.get('/')
print(net_discovery.json())

print(net_adap.get('/v2.0/networks').json())
# ks = client.Client(session=sess)
# users = ks.users.list()

            # _auth.get_auth_ref(_session) # should get a token
            # _session.get_endpoint(service_type='identity')
