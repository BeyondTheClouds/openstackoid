# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative

import copy
import json
import logging
import os
import unittest
from unittest import TestCase, mock

from requests import Request

from oidinterpreter import (OidInterpreter, get_oidinterpreter, oss2services,
                            SCOPE_DELIM)


LOG = logging.getLogger('oidinterpreter')
LOG.setLevel(int(os.environ.get('LOG_LEVEL', logging.WARNING)))


SERVICES = [{'Interface': 'admin', 'Region': 'CloudOne',
             'Service Type': 'identity',
             'URL': 'http://192.168.141.245:8888/identity'},
            {'Interface': 'public', 'Region': 'CloudOne',
             'Service Type': 'identity',
             'URL': 'http://192.168.141.245:8888/identity'},
            {'Interface': 'public', 'Region': 'CloudOne',
             'Service Type': 'compute',
             'URL': 'http://192.168.141.245:8888/compute/v2.1'},
            {'Interface': 'admin', 'Region': 'CloudTwo',
             'Service Type': 'identity',
             'URL': 'http://192.168.142.245:8888/identity'},
            {'Interface': 'public', 'Region': 'CloudTwo',
             'Service Type': 'identity',
             'URL': 'http://192.168.142.245:8888/identity'},
            {'Interface': 'public', 'Region': 'CloudTwo',
             'Service Type': 'compute',
             'URL': 'http://192.168.142.245:8888/compute/v2.1'}]


class TestInterpreter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        the_services = oss2services(SERVICES)
        cls.the_oidi = OidInterpreter(the_services)
        cls.the_i1service = the_services[0]  # Identity@CloudOne
        cls.the_i2service = the_services[3]  # Identity@CloudTwo
        cls.the_c1service = the_services[2]  # Compute@CloudOne
        cls.the_c2service = the_services[5]  # Compute@CloudTwo
        cls.the_token = '507582fc-57c6-4bc7-a051-9fb3f269da70'

    def test_lookup_service(self):
        # Lookup `the_c2service` by interface, service_type, region
        res_service = self.the_oidi.lookup_service(
            lambda s:
                s.interface == self.the_c2service.interface and
                s.service_type == self.the_c2service.service_type and
                s.cloud == self.the_c2service.cloud)

        self.assertEqual(res_service, self.the_c2service)

        # Lookup `the_c2service` by URL
        req = Request('GET', self.the_c2service.url)
        res_service = self.the_oidi.lookup_service(
            lambda s: req.url.startswith(s.url))

        self.assertEqual(res_service, self.the_c2service)

        # Bad lookup
        with self.assertRaises(StopIteration):
            self.the_oidi.lookup_service(lambda s: False)

    def test_is_scoped_url(self):
        # `the_c2service` is scoped
        res_service = self.the_oidi.is_scoped_url(
            Request('GET', self.the_c2service.url))
        self.assertEqual(res_service, self.the_c2service)

        # `wikipedia.org` is not a scoped service
        self.assertFalse(self.the_oidi.is_scoped_url(
            Request('GET', 'https://wikipedia.org')))

    def test_get_scope(self):
        the_scope = {'identity': 'CloudOne', 'compute': 'CloudOne'}

        # Get a full scope from X-Scope header
        headers = {'X-Scope': json.dumps(the_scope)}
        req = Request('GET', self.the_c2service.url, headers)
        res_scope = self.the_oidi.get_scope(req)
        self.assertEqual(res_scope, the_scope)

        # Get a full scope from X-Auth-Token header
        headers = {
            'X-Auth-Token':
                f'{self.the_token}{SCOPE_DELIM}{json.dumps(the_scope)}'}
        req = Request('GET', self.the_c2service.url, headers)
        res_scope = self.the_oidi.get_scope(req)
        self.assertEqual(res_scope, the_scope)

        # Get a False scope in absence of one
        req = Request('GET', self.the_c2service.url, headers=None)
        res_scope = self.the_oidi.get_scope(req)
        self.assertFalse(res_scope)

        headers = {'X-Auth-Token': self.the_token}
        req = Request('GET', self.the_c2service.url, headers)
        res_scope = self.the_oidi.get_scope(req)
        self.assertFalse(res_scope)

    def test_interpret(self):
        the_scope = {'identity': 'CloudOne', 'compute': 'CloudOne'}

        # A missing scope doesn't change the request
        req = Request('GET', self.the_c2service.url, headers=None)
        self.the_oidi.interpret(req)
        self.assertEqual(req.url, self.the_c2service.url)
        self.assertDictEqual(req.headers, {})

        headers = {'X-Auth-Token': self.the_token}
        req = Request('GET', self.the_c2service.url, copy.copy(headers))
        self.the_oidi.interpret(req)
        self.assertEqual(req.url, self.the_c2service.url)
        self.assertDictEqual(req.headers, headers)

        # A non scoped service doesn't change the request
        headers = {'X-Scope': json.dumps(the_scope)}
        req = Request('GET', 'https://wikipedia.org', copy.copy(headers))
        self.the_oidi.interpret(req)
        self.assertEqual(req.url, 'https://wikipedia.org')
        self.assertDictEqual(req.headers, headers)

        # Compute@CloudTwo + Scope Compute@CloudOne ⇒ Compute@CloudOne
        headers = {'X-Scope': json.dumps(the_scope)}
        req = Request('GET', self.the_c2service.url, copy.copy(headers))
        self.the_oidi.interpret(req)
        self.assertEqual(req.url, self.the_c1service.url)

        # Scope + Identity ⇒ Delete Scope in token
        headers = {
            'X-Auth-Token':
                f'{self.the_token}{SCOPE_DELIM}{json.dumps(the_scope)}'}
        req = Request('GET', self.the_i1service.url, copy.copy(headers))
        self.the_oidi.interpret(req)
        self.assertEqual(req.url, self.the_i1service.url)
        self.assertEqual(req.headers['X-Auth-Token'], self.the_token)

    @mock.patch('builtins.open',
                mock.mock_open(read_data=json.dumps(SERVICES)))
    def test_get_oidinterpreter(self):
        # Transform OpenStack `SERVICES` into `oidinterpreter.Service`.
        the_services = oss2services(SERVICES)

        # Get an Interpreter from a file scheme
        res_oidi = get_oidinterpreter('file://./services.json')
        self.assertEqual(res_oidi.services, the_services)

        # An interpreter is a singleton
        res_oidi2 = get_oidinterpreter('file://./services.json')
        self.assertEqual(res_oidi, res_oidi2)

        # An interpreter with another URI results in a new Interpreter
        res_oidi2 = get_oidinterpreter('file://.//another-file.json')
        self.assertNotEqual(res_oidi, res_oidi2)

        # An interpreter with another URI results in a new Interpreter hence,
        # doesn't resolve the absolute path.
        fp = os.path.abspath('./services.json')
        res_oidi2 = get_oidinterpreter('file://' + fp)
        self.assertNotEqual(res_oidi, res_oidi2)


if __name__ == "__main__":
    unittest.main()
