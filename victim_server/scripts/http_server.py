#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import traceback
from datetime import datetime
from collections import defaultdict
import zlib
from urllib.parse import parse_qs
import json


class HTTPError(Exception):
    def __init__(self, code, message):
        self.message = message
        self.code = code


class ClientError(HTTPError):
    def __init__(self, message, code=400):
        super().__init__(code, message)


class Request:
    def __init__(self, method, path, headers, data=None):
        self.method = method
        self.path = path
        self.headers = headers
        self.data = data
        self._cookies = None
        self._query = None
        self._params = None

    @property
    def cookies(self):
        if self._cookies is None:
            raw_cookies = self.headers.get('cookie', [])
            self._cookies = {}
            for raw_cookie in raw_cookies:
                for cookie in raw_cookie.split(';'):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        self._cookies[key.strip()] = value.strip()
        return self._cookies

    @property
    def query(self):
        if self._query is None:
            query = self.path.split('?', 1)
            if len(query) == 2:
                query = query[1]
            else:
                query = ''
            self._query = parse_qs(query)
        return self._query

    @property
    def params(self):
        if not self._params and self.data is not None:
            self._params = parse_qs(self.data)
        return self._params

    def json(self):
        return json.loads(self.data) if self.data is not None else None


__orig_print = print


def print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    __orig_print(*args, **kwargs)


def read(n):
    return sys.stdin.buffer.read(n)


def write(data):
    return sys.stdout.buffer.write(data)


def read_until(marker, max_chars=4096):
    data = bytearray()

    while len(data) < max_chars:
        try:
            data.append(read(1)[0])
        except IndexError:
            raise ClientError("EOF")

        if data.endswith(marker):
            #print("Recved:", data)
            return data[:-len(marker)]
    #print("Max char size reached!")
    return data


def parse_request():
    first_line = read_until(b'\n')
    if first_line.endswith(b'\r'):
        endmarker = b'\r\n'
        first_line = first_line.strip()
    else:
        endmarker = b'\n'

    parts = first_line.decode().split(' ')

    if len(parts) != 3:
        raise ClientError("Invalid HTTP Request: " + first_line.decode())

    method, path, version = parts
    method = method.upper()

    if method not in ['GET', 'POST']:
        raise ClientError("Invalid HTTP Method: " + method)

    headers = defaultdict(list)

    raw_headers = read_until(endmarker + endmarker)

    for line in raw_headers.split(endmarker):
        sys.stderr.buffer.write(line + b'\n')
        key, value = line.decode().split(':', 1)
        headers[key.strip().lower()].append(value.strip())

    if 'content-length' in headers:
        length = int(headers['content-length'][-1])

        data = read(length)
    else:
        data = None
        length = 0

    print(f"[{datetime.now()}] <= {method} {path} {length}")
    return Request(method, path, headers, data)


def send_response(code, message, headers, body):
    write(f"HTTP/1.0 {code} {message}\r\n".encode())
    for key, values in headers.items():
        for value in values:
            write(f"{key}: {value}\r\n".encode())

    l = len(body)
    write(f"Content-Length: {l}\r\n\r\n".encode())
    if isinstance(body, str):
        write(body.encode())
    else:
        write(body)
    sys.stdout.buffer.flush()

    print(f"[{datetime.now()}] => {code} {message} {l}")


def send_compressed(code, message, headers, body):
    headers['Content-encoding'] = ['deflate']
    if isinstance(body, str):
        body = body.encode()
    compressed_body = zlib.compress(body)
    send_response(code, message, headers, compressed_body)


def serve(handlers):
    try:
        request = parse_request()

        path = request.path.split('?', 1)[0]
        for pattern, handler in handlers.items():
            if hasattr(pattern, 'match') and pattern.match(path):
                handler(request)
                break
            elif pattern == path:
                handler(request)
                break
        else:
            send_response(404, "Not Found", {'content-type': ['text/plain']}, "Path {} not found".format(request.path))
    except HTTPError as e:
        send_response(e.code, e.message, {'content-type': ['text/plain']}, e.message)
    except Exception as e:
        send_response(500, str(e), {'content-type': ['text/plain']}, traceback.format_exc())
