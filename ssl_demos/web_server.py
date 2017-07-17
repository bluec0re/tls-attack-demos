import logging
import asyncio
import pathlib

from aiohttp import web, protocol
import aiohttp_jinja2
import jinja2


BASE_PATH = pathlib.Path(__file__).parent


protocol.HttpMessage.SERVER_SOFTWARE = 'BlueC0re SSL DEMO SERVER'


log = logging.getLogger(__name__)


class WebServer(web.Application):
    def __init__(self, *args, **kwargs):
        super(WebServer, self).__init__(*args, **kwargs)
        self.router.add_get('/p/{plugin}', self.plugin_html)
        self.router.add_static('/static/plugins', str(BASE_PATH / "plugins" / "static"))
        self.router.add_static('/static', str(BASE_PATH / "static"))
        aiohttp_jinja2.setup(self,
                loader=jinja2.ChoiceLoader([
                    jinja2.PackageLoader('ssl_demos'),
                    jinja2.PackageLoader('ssl_demos.plugins'),
                ])
        )

    def create_server(self, host='0.0.0.0', port=8088, backlog=128):
        loop = self._loop
        self.__handler = self.make_handler()
        server = loop.create_server(self.__handler, host, port,
                                    backlog=backlog)

        log.info('Creating server on %s:%d', host, port)

        return asyncio.gather(server, self.startup(), loop=loop)

    async def stop_server(self, timeout=None):
        await self.shutdown()
        await self.__handler.finish_connections(timeout)
        await self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._loop.run_until_complete(self.stop_server())

    @aiohttp_jinja2.template('plugin.jinja2')
    def plugin_html(self, request):
        plugin = request.match_info['plugin']
        return {'plugin': plugin}

