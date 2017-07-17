#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.parse import parse_qs
from html import escape
import uuid
import hashlib
from http_server import *


SECRET = 'nuej0eeNg5ohyi1as5ohgheangoo2chaejeibaraihahlohsh4ooc9fohziep0Xoo9Eeghim1tohsaijeeb4teel3ohf9aeb6yek'

def handler(request):
    sessionid = request.cookies.get('SESSION')
    if sessionid is None:
        sessionid = str(uuid.uuid4())

    csrf_token = hashlib.sha256((sessionid + SECRET).encode()).hexdigest()
    print(csrf_token)

    headers = {
        'Content-Type': ['text/html'],
        'Set-Cookie': ['SESSION=' + sessionid],
        'X-Frame-Options': ['DENY']
    }

    affiliate = str(request.query.get('affiliate', ['None'])[0]).replace("'", '%22')

    if request.method == 'GET':
        send_compressed(200, 'Ok', headers, f"""<html>
<body>
    <h1>Secure Website</h1>
    <p>We are using TLS for communications and CSRF-Tokens for all actions</p>

    <a href='/?affiliate={affiliate}'>Some Link</a>

    <form method="post">
        <input type="hidden" name="csrftoken" value="{csrf_token}">
        <button type="submit">Do something</button>
    </form>
</body>
</html>""")
    elif request.method == 'POST':
        params = request.params
        if params.get('csrftoken') == csrf_token:
           send_compressed(200, 'Ok', headers, f"""<html>
<body>
    <h1>Secure Website</h1>
    <p>We are using TLS for communications and CSRF-Tokens for all actions</p>
    <p><span style="color: green">VALID</span> submit</p>
</body>
</html>""") 
        else:
           send_compressed(403, 'Invalid CSRF', headers, f"""<html>
<body>
    <h1>Secure Website</h1>
    <p>We are using TLS for communications and CSRF-Tokens for all actions</p>
    <p><span style="color: red">INVALID</span> submit</p>
</body>
</html>""") 


serve({'/': handler})
