from requests import Request, Session

from openstackoid.interpreter import Service, get_interpreter_from_services


# A dummy identity service is required for proper interpretation of scope
identity = Service(service_type='identity',
                   cloud='Instance1',
                   url='https://www.phony.com/',
                   interface='admin')
qwant = Service(service_type='Search Engine',
                cloud='Instance1',
                url='https://www.qwant.com/')
ddg = Service(service_type='Search Engine',
              cloud='Instance2',
              url='https://www.duckduckgo.com/')

headers = {'X-Scope': '{"Search Engine": "Instance1", "identity": "Instance1"}'}
request = Request('GET', f'{ddg.url}?q=openstackoid', headers)
session = Session()

# Here the headers are set however the scope is not used. Therefore the request
# is sent to DuckDuckGo as a plain request.
print(session.send(request.prepare()).url)

# Now the interpreter uses the scope header to update the request Interprets the
# Scope says "use rather `Search Engine` in Instance1" and transforms DuckDuckGo
# into Qwant (using immutable interpretation), so a new request is created.
interpreter = get_interpreter_from_services([identity, qwant, ddg])
irequest = interpreter.iinterpret(request)
print(session.send(irequest.prepare()).url)
