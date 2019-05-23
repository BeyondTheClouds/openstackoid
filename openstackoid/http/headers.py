# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from typing import Dict

import copy
import json

from requests import Request
from urllib import parse

import six


SCOPE_DELIMITER = "!SCOPE!"


X_AUTH_TOKEN = "X-Auth-Token"


X_IDENTITY_CLOUD = "X-Identity-Cloud"


X_IDENTITY_URL = "X-Identity-Url"


X_SCOPE = "X-Scope"


X_SUBJECT_TOKEN = "X-Subject-Token"


def sanitize_headers(headers: Dict) -> Dict[str, str]:
    """Sanitize the key/value encoding of a dictionary.

    This method is an adapted version of the method `_sanitize_headers` from
    `keystoneauth1.session` because it also fix the encoding from url strings
    with special characters.

    """

    str_dict = {}
    for k, v in headers.items():
        if six.PY3:
            k = k.decode('ASCII') if isinstance(k, six.binary_type) else k
            if v is not None:
                v = v.decode('ASCII') if isinstance(v, six.binary_type) else v

                # decode url strings with special characters
                v = parse.unquote(v)

        else:
            k = k.encode('ASCII') if isinstance(k, six.text_type) else k
            if v is not None:
                v = v.encode('ASCII') if isinstance(v, six.text_type) else v
                v = parse.unquote(v)

        str_dict[k] = v

    return str_dict


def update_service_scope(service_type: str,
                         scope: str, request: Request) -> Request:
    """Update the scope of a `request` for a specific service type.

    Immutable method to update the scope found in the headers of a `request`,
    when is set. It returns a new `Request` with the updated scope for the
    provided service type. This method does NOT set any default scope if it is
    not already available in the headers.

    """

    _request = copy.deepcopy(request)
    headers = sanitize_headers(_request.headers)
    if X_SCOPE in headers:
        scope_value = headers[X_SCOPE]
        current_scope = json.loads(scope_value)
        current_scope.update({service_type: scope})
        x_scope = json.dumps(current_scope)
        _request.headers.update({X_SCOPE: x_scope})

    if X_AUTH_TOKEN in headers:
        token = headers[X_AUTH_TOKEN]
        if SCOPE_DELIMITER in token:
            token, scope_value = token.split(SCOPE_DELIMITER)
            current_scope = json.loads(scope_value)
            current_scope.update({service_type: scope})
            scope_value = json.dumps(current_scope)
            x_auth_token = f"{token}{SCOPE_DELIMITER}{scope_value}"
            _request.headers.update({X_AUTH_TOKEN: x_auth_token})

    return _request
