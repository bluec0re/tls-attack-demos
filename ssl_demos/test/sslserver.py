import ssl
import asyncio
import pathlib
import uuid

from aiohttp import web

BASE_PATH = pathlib.Path(__file__).parent


async def index(request):
    sessionid = request.cookies.get('sessionid')
    if sessionid is None:
        sessionid = str(uuid.uuid4())
        resp = web.Response(text='Cookie set')
        resp.set_cookie('sessionid', sessionid)
    else:
        resp = web.Response(text='Session ID: {}\nTest-Parameter: {}'.format(
            sessionid,
            request.GET.get('test')
        ))

    resp.enable_compression(True)
    return resp


def main():
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    sslcontext.load_cert_chain(str(BASE_PATH / 'sample.crt'), str(BASE_PATH / 'sample.key'))

    loop = asyncio.get_event_loop()

    app = web.Application(loop=loop)
    app.router.add_get('/', index)

    handler = app.make_handler()
    srv = loop.create_server(handler, '127.0.0.1', 8443, ssl=sslcontext)
    loop.run_until_complete(srv)

    loop.run_forever()



if __name__ == "__main__":
    main()
