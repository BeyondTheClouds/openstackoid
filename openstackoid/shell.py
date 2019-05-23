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
OpenStackClient plugin for OpenStackoïd.

Adds `--oid-scope` global parameter:
--oid-scope '{
  "compute": "OS_SCOPE_COMPUTE | OS_REGION_NAME",
  "identity": "OS_SCOPE_IDENTITY | OS_REGION_NAME",
  "image": "OS_SCOPE_IMAGE | OS_REGION_NAME",
  "network": "OS_SCOPE_NETWORK | OS_REGION_NAME",
  "placement": "OS_SCOPE_PLACEMENT | OS_REGION_NAME",
}' (Env: OS_SCOPE)
"""


from osc_lib import shell

import json
import logging

from .configuration import push_shell_scope
from .http import request  # noqa
from .utils import get_default_scope


DEFAULT_API_VERSION = '1'


# API options required by the OSC plugin interface
API_NAME = 'openstackoid'


API_VERSION_OPTION = 'os_openstackoid_api_version'


API_VERSIONS = {'1': 'openstackoid.shell'}

# Hack to avoid verbose executions without flags.
logger = logging.getLogger()
while logger.handlers:
    logger.handlers.pop()


# Required by the OSC plugin interface
def build_option_parser(parser):
    """Hook to add '--oid-scope' to `openstackclient` shell options.

    Called from openstackclient.shell.OpenStackShell.__init__() after the
    builtin parser has been initialized. This is where a plugin can add global
    options such as an API version setting.

    :param argparse.ArgumentParser parser: The parser object that has been
        initialized by OpenStackShell.

    """

    def _fmt_doc(service_name):
        return (f"(Env: OS_SCOPE_{service_name.upper()} | OS_REGION_NAME)")

    parser.add_argument(
        '--oid-scope',
        metavar='<oid_scope>',
        default=get_default_scope(),
        help=("OpenStackoid Scope, "
              "default='%s'"
              % json.dumps({
                  "compute": _fmt_doc('compute'),
                  "identity": _fmt_doc('identity'),
                  "image": _fmt_doc('image'),
                  "network": _fmt_doc('network'),
                  "placement": _fmt_doc('placement')})))
    return parser


# -- Monkey-patching openstackclient --
#
# 1. Monkey-patch OpenStackShell.initialize_app to retrieve the scope value.
#
# See,
# https://github.com/openstack/osc-lib/blob/aaf18dad8dd0b73db31aa95a6f2fce431c4cafda/osc_lib/shell.py#L390
initialize_app = shell.OpenStackShell.initialize_app


def _os_shell_monkey_patch(cls, argv):
    """Get the `oid-scope` at the initialization of the app.

    Get the `oid-scope` and put it into the `OS_SCOPE` global variable for
    latter use in `Session.request`.

    """

    final_scope: dict = get_default_scope()
    shell_value = cls.options.oid_scope
    # only update scope if it is provided as 'str' in the shell
    if isinstance(shell_value, str):
        try:
            shell_scope = json.loads(shell_value)
            final_scope.update(shell_scope)
        except ValueError:
            error_msg = ('--oid-scope is not valid. see, '
                         '`openstack --help|fgrep -A 8 -- --oid-scope`')
            raise ValueError(error_msg)

    push_shell_scope(final_scope)
    cls.options.oid_scope = final_scope
    return initialize_app(cls, argv)


# override the actual method
shell.OpenStackShell.initialize_app = _os_shell_monkey_patch


# 2. Monkey-patch `Session.request` to piggyback the scope on the headers.
#
# See,
# https://github.com/requests/requests/blob/64bde6582d9b49e9345d9b8df16aaa26dc372d13/requests/sessions.py#L466
#
# All manipulations of module 'requests' are performed in the
# `openstackoid.http.request` module. By importing that module the patch is
# applied.
