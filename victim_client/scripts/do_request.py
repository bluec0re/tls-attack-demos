#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socketserver
import json
import requests
import argparse


class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            data = json.loads(self.rfile.readline())
            print(data)

            requests.request(verify=False, **data)


server = socketserver.TCPServer(('', 4444), RequestHandler)
server.serve_forever()
