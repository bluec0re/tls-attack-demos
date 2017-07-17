import argparse
import logging
import importlib
import inspect
import pkgutil
import time
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, ParseResult
from .common.sniffer import Sniffer

import requests
from requests.packages import urllib3

try:
    from helperlib.logging import default_config
except ImportError as e:
    default_config = logging.basicConfig


urllib3.disable_warnings()
log = logging.getLogger(__name__)


def _collect_plugins():
    from . import plugins
    _plugins = {}
    
    for modinfo in pkgutil.iter_modules(plugins.__path__):
        mod = modinfo.module_finder.find_module(modinfo.name).load_module(modinfo.name)
        for name, clazz in inspect.getmembers(mod, inspect.isclass):
            if not name.endswith('Plugin'):
                continue

            _plugins[name[:-len('Plugin')]] = clazz

    return _plugins


class Demos:
    available_plugins = _collect_plugins()

    def __init__(self, args):
        self.args = args

    def __getattr__(self, name):
        return getattr(self.args, name)

    def start_plugin(self, plugin_name):
        plugin = self.available_plugins[plugin_name]

        if hasattr(plugin, 'use_sniffer') and plugin.use_sniffer:
            sniffer = Sniffer(self.intf, self.ip, self.port)
            sniffer.start()
            log.info('Waiting for sniffer startup')
            time.sleep(0.5)
            p = plugin(core=self, sniffer=sniffer)
        else:
            sniffer = None
            p = plugin(core=self)
        
        try:
            p.start()
        except KeyboardInterrupt:
            if sniffer:
                log.info('Stopping sniffer')
                sniffer.stop()
                sniffer.join()

    def send(self, parameters=None, query=None, data=None, placeholders=None):
        url = urlparse(self.url)
        origquery = parse_qsl(url.query, keep_blank_values=True)

        if isinstance(data, dict):
            data = urlencode(data)
        
        if query is not None:
            if isinstance(query, dict):
                query = list(query.items())
            origquery += query

        if parameters is not None:
            if isinstance(parameters, dict):
                parameters = list(parameters.items())
            if self.method == 'GET':
                origquery += parameters.items()
            elif self.method == 'POST':
                if data is None:
                    data = urlencode(parameters)
                else:
                    data += '&' + urlencode(parameters)

        
        if placeholders is not None:            
            p2 = {}
            for name, value in placeholders.items():
                name = '{{{}}}'.format(name)
                p2[name] = value
                log.debug('Replace %s with %s', name, value)
                if data is not None:
                    data = data.replace(name, value)

            q2 = []    
            for k, v in origquery:
                if v in p2:
                    q2.append((k, p2[v]))
                else:
                    q2.append((k, v))
            origquery = q2
                
        query = urlencode(origquery)
        res = ParseResult(*(url[:4] + (query,) + url[5:]))
        url = urlunparse(res)

        self.request(self.method, url, data=data)
    
    def request(self, method, url, data=None, headers=None):
        if self.cookies:
            cookies = dict(parse_qsl(self.cookies))
        else:
            cookies = None
        log.debug('Requesting %s %s', method, url)
        requests.request(method, url, data=data, headers=headers, verify=False, cookies=cookies)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel', choices=(
        'DEBUG', 'INFO', 'WARN', 'ERROR'
    ), default='INFO')
    parser.add_argument('PLUGIN', choices=Demos.available_plugins.keys())
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('-i', '--ip')
    parser.add_argument('-I', '--intf', default='lo')
    parser.add_argument('-m', '--method', default='GET')
    parser.add_argument('-H', '--header', action='append')
    parser.add_argument('-d', '--data')
    parser.add_argument('-u', '--url')
    parser.add_argument('-c', '--charset', default='0123456789abcdef')
    parser.add_argument('-t', '--target')
    parser.add_argument('-P', '--prefix')
    parser.add_argument('-b', '--cookies')
    parser.add_argument('-s', '--start', default='')


    args = parser.parse_args(argv)
    
    default_config(level=args.loglevel)

    demos = Demos(args)
    demos.start_plugin(args.PLUGIN)

