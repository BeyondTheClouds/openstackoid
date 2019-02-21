# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative
#
# See
# - https://docs.openstack.org/python-openstackclient/latest/contributor/plugins.html

"""
OpenStackClient plugin for OpenStackoid.

Adds `--os-scope` global parameter:
--os-scope '{
  "compute": "OS_SCOPE_COMPUTE | OS_REGION_NAME",
  "identity": "OS_SCOPE_IDENTITY | OS_REGION_NAME",
  "image": "OS_SCOPE_IMAGE | OS_REGION_NAME",
  "network": "OS_SCOPE_NETWORK | OS_REGION_NAME",
  "placement": "OS_SCOPE_PLACEMENT | OS_REGION_NAME",
}' (Env: OS_SCOPE)
"""

import json
import logging
from osc_lib import utils


LOG = logging.getLogger(__name__)

DEFAULT_API_VERSION = '1'

# Required by the OSC plugin interface
API_NAME = 'openstackoid'
API_VERSION_OPTION = 'os_openstackoid_api_version'
API_VERSIONS = {
    '1': 'openstackoidclient.client',
}

DEFAULT_OS_REGION_NAME = "RegionOne"


# Required by the OSC plugin interface
def build_option_parser(parser):
    """Hook to add global options

    Called from openstackclient.shell.OpenStackShell.__init__()
    after the builtin parser has been initialized.  This is
    where a plugin can add global options such as an API version setting.

    :param argparse.ArgumentParser parser: The parser object that has been
        initialized by OpenStackShell.
    """
    def _fmt_doc(service):
        return ("%s (Env: OS_SCOPE_%s | OS_REGION_NAME)" %
                (DEFAULT_OS_REGION_NAME, service.upper()))

    parser.add_argument(
        '--os-scope',
        metavar='<os_scope>',
        default=_get_default_os_scope(),
        help=("OpenStackoid Scope, "
              "default='%s'"
              % json.dumps({
                  "compute": _fmt_doc('compute'),
                  "identity": _fmt_doc('identity'),
                  "image": _fmt_doc('image'),
                  "network": _fmt_doc('network'),
                  "placement": _fmt_doc('placement')})))

    return parser


def _get_os_scope_service_env(service):
    """Lookup for `OS_SCOPE_<service>` or `OS_REGION_NAME` env variables.

    If neither OS_SCOPE_<service> or OS_REGION_NAME are available, then this
    function returns the value of `DEFAULT_OS_REGION_NAME`.

    """
    env_name = "OS_SCOPE_%s" % service.upper()
    default = {'default': DEFAULT_OS_REGION_NAME}

    return utils.env(env_name, 'OS_REGION_NAME', **default)


def _get_default_os_scope():
    """Compute the default scope.

    Something like:
    {
      "compute": "OS_SCOPE_COMPUTE | OS_REGION_NAME",
      "identity": "OS_SCOPE_IDENTITY | OS_REGION_NAME",
      "image": "OS_SCOPE_IMAGE | OS_REGION_NAME",
      "network": "OS_SCOPE_NETWORK | OS_REGION_NAME",
      "placement": "OS_SCOPE_PLACEMENT | OS_REGION_NAME",
    }"""
    return {
        "compute": _get_os_scope_service_env('compute'),
        "identity": _get_os_scope_service_env('identity'),
        "image": _get_os_scope_service_env('image'),
        "network": _get_os_scope_service_env('network'),
        "placement": _get_os_scope_service_env('placement')
    }


# -- 🐒 Monky Patching 🐒
OS_SCOPE = None

# 1. Monkeypatch OpenStackShell.initialize_app to retrieve the scope value
#
# See,
# https://github.com/openstack/osc-lib/blob/aaf18dad8dd0b73db31aa95a6f2fce431c4cafda/osc_lib/shell.py#L390
from osc_lib import shell


init_app = shell.OpenStackShell.initialize_app
def mkeypatch_initialize_app(cls, argv):
    """Get the `os-scope` at the initialization of the app.

    Get the `os-scope` and put it into the `OS_SCOPE` global variable for
    latter use in `Session.request`.

    """
    global OS_SCOPE

    os_scope = _get_default_os_scope()
    shell_scope = cls.options.os_scope
    error_msg = ('--os-scope is not valid. see, '
                 '`openstack --help|fgrep -A 8 -- --os-scope`')

    if isinstance(shell_scope, dict):
        os_scope.update(shell_scope)
    elif isinstance(shell_scope, basestring):
        try:
            os_scope.update(json.loads(shell_scope))
        except ValueError:
            raise ValueError(error_msg)
    else:
        raise ValueError(error_msg)

    OS_SCOPE = os_scope
    LOG.info("Save the current os-scope: ", OS_SCOPE)

    # XXX(rcherrueau): We remove the `os_scope` from the list of command
    # options (i.e., `cls.options`). We have to do so because of openstack
    # config loader [1] that strips the `os_` prefix of all options [2] and
    # deduces a specific configuration for the current cloud. Unfortunately,
    # `os_scope` becomes `scope` and hence gives a value to the `scope`
    # reserved keyword (I don't know which service exactly uses that keyword,
    # maybe policy from keystone [3]).
    #
    # [1]
    # https://github.com/openstack/openstacksdk/blob/stable/rocky/openstack/config/loader.py
    # [2]
    # https://github.com/openstack/openstacksdk/blob/5b15ccf042fafa14908ff1afe5a66cbce201d9ef/openstack/config/loader.py#L775-L781
    # [3]
    # https://docs.openstack.org/keystone/rocky/configuration/samples/policy-yaml.html
    del cls.options.os_scope

    return init_app(cls, argv)
shell.OpenStackShell.initialize_app = mkeypatch_initialize_app


# 2. Monkey patch `Session.request` to piggyback the scope with the keystone
# token.
#
# See,
# https://github.com/requests/requests/blob/64bde6582d9b49e9345d9b8df16aaa26dc372d13/requests/sessions.py#L466
from requests import Session

session_request = Session.request
def mkeypatch_session_request(cls, method, url, **kwargs):
    """Piggyback the `OS_SCOPE` on `X-Auth-Token`."""
    # Retrieve headers of the request
    headers = kwargs.get('headers', {})

    # Put the scope in X-Scope header
    if OS_SCOPE:
        LOG.info("Find a os-scope %s..." % OS_SCOPE)
        os_scope_json = json.dumps(OS_SCOPE)
        headers['X-Scope'] = os_scope_json

        # Piggyback OS_SCOPE with X-Auth-Token
        if 'X-Auth-Token' in headers:
            LOG.info("...to piggyback on token %s " % headers['X-Auth-Token'])
            headers['X-Auth-Token'] = "%s!SCOPE!%s" % (headers['X-Auth-Token'], os_scope_json)
            LOG.debug("Piggyback os-scope %s" % repr(headers))

    return session_request(cls, method, url, **kwargs)
Session.request = mkeypatch_session_request
