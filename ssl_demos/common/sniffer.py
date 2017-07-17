import threading
import logging
import queue
from collections import OrderedDict

from scapy.sendrecv import sniff
from scapy.layers.inet import IP, TCP
from .packets import *


log = logging.getLogger(__name__)


class Connection:
    def __init__(self):
        self.alive = True
        self.source = None
        self.destination = None
        self.recvd = 0
        self.sent = 0
        self.tls_sent = 0
        self.tls_recvd = 0
        self.closed = 0

    def __repr__(self):
        return '{0[0]}:{0[1]} -> {1[0]}:{1[1]}'.format(self.source, self.destination)

    def key(self):
        return (self.source, self.destination)


class Sniffer(threading.Thread):
    def __init__(self, intf, target_ip, target_port):
        super().__init__()
        self.interface = intf
        self.target_ip = target_ip
        self.target_port = target_port
        self.closed_connections = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()
        self.connections = OrderedDict()
        self.connections_sem = threading.Semaphore()

    def run(self):
        log.info('Starting sniffer for %s:%d on %s', self.target_ip, self.target_port, self.interface)
        sniff(
            iface=self.interface,
            prn=self.process,
            filter='ip host {} and tcp port {}'.format(
                self.target_ip,
                self.target_port
            ),
            stop_filter=lambda p: self.stop_event.is_set()
        )

    def stop(self):
        self.stop_event.set()

    def has_conn(self, key):
        with self.connections_sem:
            return key in self.connections

    def get_conn(self, key):
        with self.connections_sem:
            return self.connections[key]
    
    def add_conn(self, key, conn):
        with self.connections_sem:
            self.connections[key] = conn

    def get_or_add_conn(self, key):
        if self.has_conn(key):
            return self.get_conn(key)
        else:
            key = key[::-1]
            if self.has_conn(key):
                return self.get_conn(key)
            else:
                log.warning('Unknown connection %r', key)
                conn = Connection()
                conn.source = key[0]
                conn.destination = key[1]
                self.add_conn(key, conn)
                return conn

    def close_conn(self, key):
        with self.connections_sem:
            conn = self.connections[key]
            closed = not conn.alive
            conn.alive = False
            conn.closed += 1
            return conn, closed

    def check_closed(self, key):
        with self.connections_sem:
            conn = self.connections[key]
            if conn.closed == 1:
                log.debug('Add closed connection: %r', conn)
                self.closed_connections.put(conn)

    def get_connection(self, packet):
        ip_packet = packet[IP]
        tcp_packet = packet[TCP]
        source_ip = ip_packet.src
        dest_ip = ip_packet.dst
        source_port = tcp_packet.sport
        dest_port = tcp_packet.dport
        closed = False

        # new connection
        if tcp_packet.flags & 0x12 == 0x12: # SYN+ACK
            conn = Connection()
            conn.source = (dest_ip, dest_port)
            conn.destination = (source_ip, source_port)
            if self.has_conn(conn.key()):
                # log.warning('Connection already opened: %r', conn)
                pass
            else:
                self.add_conn(conn.key(), conn)
                log.debug('Captured conn start (resp) %r', conn)
        elif tcp_packet.flags & 0x2: # SYN
            conn = Connection()
            conn.source = (source_ip, source_port)
            conn.destination = (dest_ip, dest_port)
            if self.has_conn(conn.key()):
                # log.warning('Connection already opened: %r', conn)
                pass
            else:
                self.add_conn(conn.key(), conn)
                log.debug('Captured conn start (req) %r', conn)
        # closing connection
        elif tcp_packet.flags & 0x11 == 0x11: # FIN+ACK
            source = (source_ip, source_port)
            destination = (dest_ip, dest_port)
            key = (source, destination)
            conn = self.get_or_add_conn(key)
            conn, closed = self.close_conn(conn.key())
            log.debug('Captured conn close (FA) %r: %r', closed, conn)
        elif tcp_packet.flags & 0x1: # FIN
            source = (source_ip, source_port)
            destination = (dest_ip, dest_port)
            key = (source, destination)
            conn = self.get_or_add_conn(key)
            conn, closed = self.close_conn(conn.key())
            log.debug('Captured conn close (F) %r: %r', closed, conn)
        elif tcp_packet.flags & 0x4: # RST
            source = (source_ip, source_port)
            destination = (dest_ip, dest_port)
            key = (source, destination)
            conn = self.get_or_add_conn(key)
            conn, closed = self.close_conn(conn.key())
            log.debug('Captured conn reset %r: %r', closed, conn)
        # other
        else:
            source = (source_ip, source_port)
            destination = (dest_ip, dest_port)
            key = (source, destination)
            conn = self.get_or_add_conn(key)
        return conn, closed

    def process(self, packet):
        log.debug('Got packet')
        if TCP in packet:
            conn, closed = self.get_connection(packet)
            ip_packet = packet[IP]
            tcp_packet = packet[TCP]

            length = ip_packet.len - len(tcp_packet)

            tcp_packet.decode_payload_as(TLSPacket)

            log.debug('Packet: %s', packet.summary())
            if TLSApplicationData in tcp_packet:
                appdata = tcp_packet[TLSApplicationData]
                log.debug('Is appdata')
            else:
                appdata = None

            
            if ip_packet.src == conn.source[0] and tcp_packet.sport == conn.source[1]: # request
                conn.sent += length
                if appdata is not None:
                    length = appdata.underlayer.length
                    log.debug('Sent %d TLS data', length)
                    conn.tls_sent += length
            else: # response
                conn.recvd += length
                if appdata is not None:
                    length = appdata.underlayer.length
                    log.debug('Received %d TLS data', length)
                    conn.tls_recvd += length

            self.check_closed(conn.key())