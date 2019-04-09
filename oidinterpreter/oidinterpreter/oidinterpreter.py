# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative

import copy
from dataclasses import dataclass
import json
import logging
import os
from typing import (Callable, Dict, List, NewType, Union)
from urllib.parse import urlparse

from requests import Request


# A service contains `Interface`, `Region`, `Service Type`, and `URL` keys.
Scope = NewType('Scope', Dict[str, str])

logging.basicConfig()
LOG = logging.getLogger(__name__)
SCOPE_DELIM = "!SCOPE!"
SCOPE_INTERPRETERS = {}


@dataclass
class Service:
    service_type: str
    cloud: str
    url: str
    interface: str = None


def oss2services(oss: List[Dict[str, str]]) -> List[Service]:
    """Transforms a list of OpenStack services into a list of Service.

    A list of OpenStack service may be obtain with

    openstack endpoint list --format json \
      -c "Service Type" -c "Interface" -c "URL" -c "Region"

    And then transformed into a python Dict with `json.load`.
    """
    return [Service(service_type=s["Service Type"],
                    cloud=s["Region"],
                    url=s["URL"],
                    interface=s["Interface"])
            for s in oss]


class OidInterpreter:
    """Interprets the `Scope` in a `Request` and update it."""

    def __init__(self, services: List[Service]):
        """Private: Use `get_oidinterpreter instead`."""
        self.services = services
        LOG.info(f'New OidInterpreter instance')

    def lookup_service(self, p: Callable[[Service], bool]) -> Service:
        """Finds the first Service that satisfies `p`.

        Looks-up into the list of services to find the first Service that
        satisfies the `p` predicate. `p` is a lambda that take a Service and
        returns a boolean. Raises `StopIterarion` if no service has been found.

        """
        try:
            service = next(s for s in self.services if p(s))
            LOG.info(f'Lookup finds service {service} with predicate {p}')
            return service
        except StopIteration as s:
            LOG.info(f'No service found with predicate {p}')
            raise s

    def is_scoped_url(self, req: Request) -> Union[Service, "False"]:
        """Tests if the `req` targets a Service.

        Returns the Service targeted by `req` if any, or False otherwise.

        """
        service = False

        try:
            service = self.lookup_service(
                lambda s: req.url.startswith(s.url))
        finally:
            return service

    def get_scope(self, req: Request) -> Union[Scope, "False"]:
        """Finds the Scope from the current Request.

        Seeks for the Scope in headers of `req`. Looks first into `X-Scope`,
        then into `X-Auth-Token` delimited by `SCOPE_DELIM`. Returns either the
        scope if found or False otherwise.

        """
        scope = False

        if 'X-Scope' in req.headers:
            scope = json.loads(req.headers.get('X-Scope'))
        elif 'X-Auth-Token' in req.headers \
             and SCOPE_DELIM in req.headers['X-Auth-Token']:
            auth_token = req.headers.get('X-Auth-Token')
            _, auth_scope = auth_token.split(SCOPE_DELIM)
            scope = json.loads(auth_scope)

        LOG.info(f'Find scope {scope} in request headers')
        return scope

    def clean_token_header(self, req: Request, token_header_name: str) -> None:
        """Cleans the token of `token_header_name` from the Scope in `req`.

        Updates `req` header in place.

        token_header_name is any valid header name that contains a keystone
        token (e.g., X-Auth-Token, X-Subject-Token).

        """
        if token_header_name in req.headers:
            auth_token = req.headers.get(token_header_name)
            token, _ = auth_token.split(SCOPE_DELIM)
            req.headers.update({token_header_name: token})
            LOG.info(f'Revert {token_header_name} to {token}')

    def interpret(self, req: Request) -> None:
        """Finds & interprets the scope to update `req` if need be.

        Update `req` in place with the new headers and url.
        """
        # Get the scope and the service originally targeted
        scope = self.get_scope(req)
        service = self.is_scoped_url(req)

        # The current request doesn't have a scope or doesn't target a scoped
        # service, so we don't change the request
        if not scope or not service:
            return

        # Find the targeted cloud
        targeted_service_type = service.service_type
        targeted_interface = service.interface
        targeted_cloud = scope[targeted_service_type]

        # From targeted cloud, find the targeted service
        targeted_service = self.lookup_service(
            lambda s:
                s.interface == targeted_interface and
                s.service_type == targeted_service_type and
                s.cloud == targeted_cloud)

        # Update request
        req.url = req.url.replace(
            service.url, targeted_service.url) # Change url
        self.clean_token_header(req, 'X-Subject-Token')  # Remove scope
        if targeted_service_type == 'identity':          # from token
            self.clean_token_header(req, 'X-Auth-Token')
        req.headers.update({
            'X-Scope': json.dumps(scope),
        })

        # HACK: Find the identity service. This part is used later to add
        # helpful headers to tweak the keystone middleware
        try:
            id_service = self.lookup_service(
                lambda s:
                    s.interface == 'admin' and
                    s.service_type == 'identity' and
                    s.cloud == scope['identity'])

            req.headers.update({
                'X-Identity-Cloud': id_service.cloud,
                'X-Identity-Url': id_service.url,
            })
        except StopIteration:
            pass

    def iinterpret(self, req: Request) -> Request:
        "Immutable version of `interpret`."
        req2 = copy.deepcopy(req)
        self.interpret(req2)
        return req2


def get_oidinterpreter(services_uri: str) -> OidInterpreter:
    """Factory method that instantiates a new OidInterpreter.

    services_uri is the url of the services list. In absence of scheme, the
    Default is `file://` uri that should target a json file.

    Right now, we only support filepath uri.

    """
    services = []
    uri = urlparse(services_uri)

    if uri not in SCOPE_INTERPRETERS:
        # Interpret the uri to get the service list. E.g.,
        # if uri.scheme == 'sql', uri.scheme == 'file' ...
        # Right now, we only support filepath uri
        fp = os.path.abspath(''.join([uri.netloc, uri.path]))
        with open(fp, 'r') as services_json:
            services = oss2services(json.load(services_json))
            LOG.debug(f'Loaded from {services_uri} the services {services}')

    # Instantiate & serialize the OidInterpreter
    return SCOPE_INTERPRETERS.setdefault(uri, OidInterpreter(services))


def get_oidinterpreter_from_services(
       services: List[Service]) -> OidInterpreter:
    """Factory method that instantiates a new OidInterpreter from a list of
service.

    """
    return OidInterpreter(services)
