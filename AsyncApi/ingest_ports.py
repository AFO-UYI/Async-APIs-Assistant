"""Here is defined the methods for Request and Ingest Port Nodes."""


import aiohttp
# from asyncio import open_connection
from functools import partial


async def http_request(url, is_a_json_returned=False, headers=None, data=None, json=None, params=None, *, request_type):
    """Manage HTTP request to certain URL. returns plain text or a parsed json according if is_a_json_returned is set
    True or False. headers must be a dictionary with header types as keyword and header values as values.
    data is a string and will be the request body. json is a dictionary passed as a shortcut to send jsons throw request
    without need a header of content-type: application/json. params is a dictionary that will be printed on URL
    as GET params. Eg: {param:value} = ?param=value"""
    async with aiohttp.ClientSession() as session:
        async with getattr(session, request_type)(url, headers=headers, data=data, json=json, params=params) as resp:
            if is_a_json_returned:
                return await resp.json()
            else:
                return await resp.text()


ingest_http_ports = {'GET': partial(http_request, request_type='get'),
                     'POST': partial(http_request, request_type='post'),
                     'PUT': partial(http_request, request_type='put'),
                     'DELETE': partial(http_request, request_type='delete')}


async def websocket(url):
    """return an instance of websocket object"""
    return await aiohttp.ClientSession().ws_connect(url)


"""
With asyncio plain connection a WinError 10053 is raised. Apparently is an aborted connection from servers.
I find out there are asyncio sockets from asyncio loops instead of asyncio root, but its needs protocols
factories according to https://docs.python.org/3/library/asyncio-eventloop.html#opening-network-connections

This will be delayed until Cython will be studied with plain sockets on C++ or some python library.


async def socket(url, port, bit_size=4098):
    new_socket = Socket(bit_size)
    await new_socket.connect(url, port)
    return new_socket


class Socket:
    def __init__(self, bit_size):
        self._writer = None
        self._reader = None
        self.is_open = True
        self._bit_size = bit_size

    async def connect(self, url, port):
        self._reader, self._writer = await open_connection(url, port)

    async def read_msg(self):
        mensaje = await self._reader.read(self._bit_size)
        return mensaje.decode('utf-8')

    async def send_str(self, message):
        self._writer.write(message.encode('utf-8'))

    async def close(self):
        self.is_open = False
        self._writer.close()
"""
