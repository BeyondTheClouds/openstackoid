# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, NewType, Tuple
from os import path

from requests import Request
from urllib import parse

import copy
import json
import logging

from .http.headers import (SCOPE_DELIMITER, X_AUTH_TOKEN, X_IDENTITY_CLOUD,
                           X_IDENTITY_URL, X_SCOPE, X_SUBJECT_TOKEN,
                           sanitize_headers)


logger = logging.getLogger(__name__)


Scope = NewType('Scope', Dict[str, str])


SCOPE_INTERPRETERS: Dict = {}


@dataclass
class Service:
    service_type: str
    cloud: str
    url: str
    interface: str


def _oss2services(services: List[Dict[str, str]]) -> List[Service]:
    """Transform a list of OpenStack services into a list of type `Service`.

    A list of OpenStack services may be obtained with:

    > openstack endpoint list --format json \
      -c "Service Type" -c "Interface" -c "URL" -c "Region"

    And then transformed into a python `dict` with `json.load`.

    """

    return [Service(service_type=s["Service Type"],
                    cloud=s["Region"],
                    url=s["URL"],
                    interface=s["Interface"])
            for s in services]


class OidInterpreter:
    """Interpret the `Scope` in a `Request` and update it."""

    def __init__(self, services: List[Service]):
        """
        Private: Use `get_interpreter instead`.

        """

        logging.debug(f'New OidInterpreter instance')
        self.services = services

    def lookup_service(self, predicate: Callable[[Service], bool]) -> Service:
        """Find the first `Service` that satisfies the `predicate`.

        Look up into the list of services to find the first `Service` that
        satisfies the `predicate`. The `predicate` is a `Callable` (or lambda)
        that receives a `Service` and returns a Boolean. The method raises
        `StopIterarion` if no `Service` has been found.

        """

        try:
            service = next(s for s in self.services if predicate(s))
            logging.debug(f"Service lookup found: {service}")
            return service
        except StopIteration as s:
            logging.error(f"No service found during lookup")
            raise s

    def get_service(self, request: Request) -> Optional[Service]:
        """Test if the `request` targets a `Service`.

        Returns the `Service` targeted by `request` if any.

        """

        service = None
        try:
            service = self.lookup_service(
                lambda s: request.url.startswith(s.url))
        finally:
            logging.debug(f"Scoped URL service: {service}")
            return service

    def get_scope(self, request: Request) -> Optional[Scope]:
        """Find the `Scope` from a `Request`.

        Seek for the `Scope` in headers of `request`. First, look into the
        header 'X-Scope', then into header 'X-Auth-Token' delimited by
        `SCOPE_DELIMITER`. and return if any.

        """

        current_scope = None
        logger.info(request.url)
        logger.info(request.headers)
        headers = sanitize_headers(request.headers)

        if X_SCOPE in headers:
            scope_value = headers[X_SCOPE]
            current_scope = json.loads(scope_value)
            logging.debug("Get scope from X-Scope")
        if X_AUTH_TOKEN in headers:
            token = headers[X_AUTH_TOKEN]
            if SCOPE_DELIMITER in token:
                token, scope_value = token.split(SCOPE_DELIMITER)
                current_scope = json.loads(scope_value)
                logging.debug("Get scope from X-Auth-Token")

        if not current_scope:
            logging.warning("Any scope found in headers")
        else:
            logging.debug(f"Scope from headers: {current_scope}")

        return current_scope

    def get_scope_faulty(self, request: Request) -> Optional[Scope]:
        from .utils import get_default_scope
        logger.info(request.url)
        logger.info(request.headers)
        final_scope = get_default_scope()
        headers = sanitize_headers(request.headers)
        if X_SCOPE in headers:
            scope_value = headers[X_SCOPE]
            current_scope = json.loads(scope_value)
            final_scope = dict(final_scope, **current_scope)
            x_scope = json.dumps(final_scope)
            request.headers.update({X_SCOPE: x_scope})
            logging.debug("Set scope from X-Scope")
        if X_AUTH_TOKEN in headers:
            token = headers[X_AUTH_TOKEN]
            if SCOPE_DELIMITER in token:
                token, scope_value = token.split(SCOPE_DELIMITER)
                current_scope = json.loads(scope_value)
                final_scope = dict(final_scope, **current_scope)
                logging.debug("Set scope from X-Auth-Token")

            scope_value = json.dumps(final_scope)
            x_auth_token = f"{token}{SCOPE_DELIMITER}{scope_value}"
            request.headers.update({X_AUTH_TOKEN: x_auth_token})

        logging.info(f"Scope from headers: {final_scope}")
        return final_scope

    def clean_token_header(self, request: Request,
                           token_header_name: str) -> None:
        """Clean the appended scope from a `request` header containing a token.

        The `token_header_name` is any valid header name that contains a
        Keystone token (e.g., X-Auth-Token, X-Subject-Token). In Openstackoid
        the scope may be appended to a token separated by the `SCOPE_DELIMITER`.
        The method updates `request` header in place.

        """

        headers = sanitize_headers(request.headers)
        if token_header_name in headers:
            auth_token = headers[token_header_name]
            if SCOPE_DELIMITER in auth_token:
                token, _ = auth_token.split(SCOPE_DELIMITER)
                request.headers.update({token_header_name: token})
                logging.debug(f"Revert '{token_header_name}' to {token}")

    def get_service_scope(self, request: Request) -> Optional[Tuple]:
        """Get the service scope of a targeted service.

        """

        scope = self.get_scope(request)
        service = self.get_service(request)
        if service:
            return service.service_type, scope[service.service_type]

        return None

    def interpret(self, request: Request, endpoint: str = None) -> None:
        """Update the `request` after interpretation of its scope.

        Find and interpret the scope in the `request`. Then, update the
        `request` in place with new headers and an updated url. If the
        `endpoint` is set do not resolve the cloud name and use the provided
        endpoint instead.

        """

        # Get the scope and the service originally targeted
        scope = self.get_scope(request)
        service = self.get_service(request)

        # The current request doesn't target a scoped service,
        # so we don't change the request
        if not service:
            logging.debug("Any scoped service found for the request")
            return

        # Find the targeted cloud
        targeted_service_type = service.service_type
        targeted_interface = service.interface

        # In simple situations (when the scope does not contain an expression,
        # i.e., scope without operators) the cloud endpoint is the name of the
        # identifier set in the scope of the original scoped/targeted service.
        targeted_cloud = endpoint if endpoint else scope[targeted_service_type]
        logging.debug(f"Effective endpoint: {targeted_cloud}")

        # From targeted cloud, find the targeted service
        targeted_service = self.lookup_service(
            lambda s:
                s.interface == targeted_interface and
                s.service_type == targeted_service_type and
                s.cloud == targeted_cloud)

        # Update request
        # 1. Change url
        request.url = request.url.replace(service.url, targeted_service.url)
        # 2. Remove scope from token
        self.clean_token_header(request, X_SUBJECT_TOKEN)
        if targeted_service_type == "identity":
            self.clean_token_header(request, X_AUTH_TOKEN)

        # 3. Update contents
        request.headers.update({X_SCOPE: json.dumps(scope)})

        # HACK: Find the identity service. This part is used later to add
        # helpful headers to tweak the `keystonemiddleware`.
        #
        # The system env var OS_REGION_NAME must be defined to get the proper
        # default scope
        if targeted_service_type == "identity":
            identity_scope = scope["identity"]
            try:
                id_service = self.lookup_service(
                    lambda s:
                        s.interface == "admin" and
                        s.service_type == "identity" and
                        s.cloud == identity_scope)

                request.headers.update({
                    X_IDENTITY_CLOUD: id_service.cloud,
                    X_IDENTITY_URL: id_service.url
                })
                logger.debug(f"Update headers {X_IDENTITY_CLOUD} "
                             f"and {X_IDENTITY_URL}")
            except StopIteration:
                logging.error(f"Invalid identity scope: {identity_scope}")
                raise ValueError

    def iinterpret(self, request: Request, endpoint: str = None) -> Request:
        """Immutable version of `interpret`.

        """
        _request = copy.deepcopy(request)
        self.interpret(_request, endpoint=endpoint)
        return _request


def get_interpreter(url: str) -> OidInterpreter:
    """Instantiate a new OidInterpreter loading services from an abstract path.

    This method is a factory. The `url` is the path to the services list. In
    absence of scheme, the default one is `file://`. The uri targets a json
    file.

    Right now, we only support filepath uri.

    """

    services: List[Service] = []
    uri = parse.urlparse(url)
    if uri not in SCOPE_INTERPRETERS:
        # Interpret the uri to get the service list. E.g.,
        # if uri.scheme == 'sql', uri.scheme == 'file' ...
        # Right now, we only support filepath uri
        file_path = path.abspath(''.join([uri.netloc, uri.path]))
        with open(file_path, 'r') as json_file:
            _services = json.load(json_file)
            services = _oss2services(_services)
            logging.debug(f"Load from {url} the services: {services}")

    # Instantiate & serialize the OidInterpreter
    return SCOPE_INTERPRETERS.setdefault(uri, OidInterpreter(services))


def get_interpreter_from_services(
       services: List[Service]) -> OidInterpreter:
    """OidInterpreter factory from a list of services.

    """

    return OidInterpreter(services)
