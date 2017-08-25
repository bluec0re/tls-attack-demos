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

    headers = {
        'Content-Type': ['text/html'],
        'Set-Cookie': ['SESSION=' + sessionid],
        'X-Frame-Options': ['DENY']
    }

    affiliate = str(request.query.get('affiliate', ['None'])[0]).replace("'", '%22')

    send_response(200, 'Ok', headers, f"""<html>
<body>
    <h1>Secure Website</h1>
    <p>We are using TLS for communications and CSRF-Tokens for all actions</p>

    <a href='/?affiliate={affiliate}'>Some Link</a>

</body>
</html>""")


serve({'/': handler})
