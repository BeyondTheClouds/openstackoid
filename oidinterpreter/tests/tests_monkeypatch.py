import copy
import requests as r

from oidinterpreter import Service, get_oidinterpreter_from_services

qwant = Service(
    service_type='Search Engine', cloud='Instance1',
    url='https://www.qwant.com/')
ddg = Service(
    service_type='Search Engine', cloud='Instance2',
    url='https://www.duckduckgo.com/')



def monkey_patch():
    oidi = get_oidinterpreter_from_services([qwant, ddg])

    r.sessions.Session.old_send = r.sessions.Session.send

    def my_send(self, request, **kwargs):
        oidi.interpret(request)
        return self.old_send(request, **kwargs)
    r.sessions.Session.send = my_send

#from openstackoid.oidinterpreter import monkey_patch

monkey_patch()

#headers = {'X-Scope': '{"Search Engine": "Instance1"}'}
req = r.Request('GET', f'{ddg.url}?q=openstackoid', headers)
s = r.Session()

prep_req = req.prepare()
response = s.send(prep_req)
