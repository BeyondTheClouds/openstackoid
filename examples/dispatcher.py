import json
import functools
import logging

from requests import Request, Session

import urllib3

from openstackoid import dispatcher
from openstackoid.requests.send import send_scope
from openstackoid.interpreter import Service, get_interpreter_from_services


logging.basicConfig(format='\t%(levelname)s\t: %(message)s')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Example I. Annotation of request using the implemented `session_scope`.
# Only Instance2 has [200] response


# A dummy identity service is required for proper interpretation of scope
identity = Service(service_type='identity',
                   cloud='Instance0',
                   url='https://www.phony.com/',
                   interface='admin')
# dukduckgo instead of duckduckgo (without first 'c') for a 403 response
invalid = Service(service_type='Search Engine',
                  cloud='Instance1',
                  url='https://www.dukduckgo.com/')
qwant = Service(service_type='Search Engine',
                cloud='Instance2',
                url='https://www.qwant.com/')
duckduckgo = Service(service_type='Search Engine',
                     cloud='Instance3',
                     url='https://www.duckduckgo.com/')
rddg = Service(service_type='Search Engine',
               cloud='Instance4',
               url='https://duckduckgo.com/')

services = [identity, invalid, qwant, duckduckgo, rddg]
interpreter = get_interpreter_from_services(services)
Session.send = send_scope(interpreter)(Session.send)

# narrow_scope = "Instance1 & ((Instance3 | Instance2) & (Instance1 | Instance3)) | Instance2"
narrow_scope = "Instance2 & Instance1 & Instance2 | Instance2 & Instance1 | Instance4"
narrow_scope = "(Instance3 & Instance1) | Instance2"
narrow_scope = "Instance2 & (Instance3 | Instance1)"
narrow_scope = "Instance2 | Instance1 & Instance3"
# narrow_scope = "Instance3 | Instance2"
# narrow_scope = "Instance2"

scope = {'Search Engine': narrow_scope, 'identity': 'Instance0'}
headers = {'X-Scope': json.dumps(scope)}
request = Request('GET', f'{duckduckgo.url}?q=discovery', headers)

session = Session()
prepared_request = session.prepare_request(request)

# ATTENTION with re-directions the behaviour is really strange and
# it fails. However this will work (need more digging on 'sessions'):
#
# session_send = send_scope(interpreter)(Session.send)
# response = session_send(session, prepared_request)
response = session.send(prepared_request, verify=False, allow_redirects=False)
print(response)


# Example II. Basic annotation with a simple function and NO interpretation
def test_extr_scp_func(*args, **kwargs):
    return 'L|R'


def test_disj_res_func(this, other):
    this.result = this.result + other.result
    return this


def test_conj_res_func(this, other):
    this.result = this.result * other.result
    return this


# Method 1.
# Decorate directly the method with scope
@dispatcher.scope(
    interpreter,
    extr_scp_func=test_extr_scp_func,
    disj_res_func=test_disj_res_func,
    conj_res_func=test_conj_res_func)
def non_factorial(n, nn=0, *args, **kwargs):
    f = 1
    while(n):
        f = f * n
        n = n - 1
    return f


# Method 2.
# Use a partial function resulting in a pre-formatted decorator
scope_tail_factorial = functools.partial(
    dispatcher.scope,
    extr_scp_func=test_extr_scp_func,
    disj_res_func=test_disj_res_func,
    conj_res_func=test_conj_res_func)


@functools.lru_cache(maxsize=2)
@scope_tail_factorial(interpreter)
def factorial(n):
    return 1 if n == 0 else n * factorial(n - 1)


@functools.lru_cache(maxsize=2)
def tail_factorial(n, r=1):
    return r if n <= 1 else tail_factorial(n - 1, n * r)


# Method 3.
# Reassign the method with a decorator method invocation (throws partial)
tail_factorial = scope_tail_factorial(interpreter)(tail_factorial)


# Execution of three methods of scoping for factorial example
n = 3


print("Non factorial")
r = non_factorial(n, nn=2, toto=3)
print(r)


print("Factorial")
r = factorial(n)
print(r)


print("Tail factorial")
r = tail_factorial(n)
print(r)
