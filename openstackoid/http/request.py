# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from requests import Response, Session

import json
import logging

from .headers import SCOPE_DELIMITER, X_AUTH_TOKEN, X_SCOPE, sanitize_headers
from .hooks import print_request_info
from ..configuration import get_shell_scope, get_execution_scope


logger = logging.getLogger(__name__)


session_request = Session.request


def _session_request_monkey_patch(cls, method, url, **kwargs) -> Response:
    """Piggyback the scope on headers of the `Session.request` method.

    """

    logger.warning("Monkey patching 'Session.request'")
    headers = kwargs.pop("headers")
    headers = sanitize_headers(headers) if headers else {}
    shell_scope = get_shell_scope()
    execution_scope = get_execution_scope()
    if execution_scope:
        service_type = execution_scope[0]
        shell_scope.update({service_type: execution_scope[1]})

    scope_value = json.dumps(shell_scope)

    # Set the scope in the X-Scope header (there is always a scope)
    headers[X_SCOPE] = scope_value
    logger.info(f"Set the X-Scope header with {scope_value}")

    # Piggyback the scope within the X-Auth-Token header
    if X_AUTH_TOKEN in headers:
        token = headers[X_AUTH_TOKEN]
        x_auth_token = f"{token}{SCOPE_DELIMITER}{scope_value}"
        headers[X_AUTH_TOKEN] = x_auth_token
        logger.info(f"Update the X-Auth-Token by appending the scope")

    logger.debug(f"Piggyback headers with the scope: {repr(headers)}")

    # Update kwargs with popped headers for proper request dispatch
    return session_request(cls, method, url,
                           hooks={"response": print_request_info},
                           headers=headers, **kwargs)


# Override the Session.request method with the monkey patch
Session.request = _session_request_monkey_patch
