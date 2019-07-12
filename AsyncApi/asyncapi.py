"""root of Async API Assistance. Here is defined the basic architecture idea and gather utilities from other files"""

from functools import partial
from aiohttp import WSMsgType

import AsyncApi.ingest_ports as ingest_ports
import AsyncApi.Errors as Errors
import AsyncApi.event_filter as event_filter


"""APIHandler architecture parts"""
API_NODES = ['ingest_port',
             'pre_processor',
             'processor',
             'request',
             'trigger']


def create_api_handler():
    """returns a new APIHandler object"""
    return APIHandler()


class APIHandler:
    """Calling APIHandler methods you will compose the handlers behaviour"""
    def __init__(self):
        self._node_types = {api_node: {} for api_node in API_NODES}

        self.get_ = {api_node: partial(self._get_node, api_node) for api_node in API_NODES}

        self._websockets = {}
        self._sockets = {}
        self._event_filters = {}

    def _define_api_handler_node(self, handler_node_type, handler_node_name, handler_node):
        """Get the function decorated and store it into _node_types, handler_node_type define to which part
         of the architecture is that function, handler_node_name is the alias of the function and handler_node
         is the function itself"""
        try:
            is_defined_yet = self._node_types[handler_node_type].get(handler_node_name, False)
        except KeyError:
            raise Errors.BadNodeType(handler_node_type)

        if not is_defined_yet:
            self._node_types[handler_node_type][handler_node_name] = handler_node
        else:
            raise Errors.AttempToOverwrite(handler_node_type, handler_node_name)

    def define_node(self, node_type, alias=None):
        """Is an interface to _define_api_handler_node. To manage the case when no alias is passed throw decorator"""
        if alias:
            return partial(self._define_api_handler_node, node_type, alias)
        else:
            def decorator(func):
                self._define_api_handler_node(node_type, func.__name__, func)

            return decorator

    def _get_node(self, node_type, node_name):
        """return functions defined at define_node. This method is an interface to self.get_, where you must pass
        node_type as dictionary keyword, and a node_name as function param. That return the reference of the function.
        You can also run that function with another parenthesis with proper params. Eg:
        apihandler.get_['processor'](processor_name)(processor_args)"""

        node_function = self._node_types[node_type].get(node_name, _missed_node)

        if node_function is _missed_node:
            node_function(node_type, node_name)
        else:
            return node_function

    """Because Events are the closest part to Triggers, and triggers are the less attached parts to APIs, the way to 
    handle events must be different, enclosing it to an JSON ingest capability approach.
     Triggers config will be those JSONs"""

    def define_event(self, event_name, event_frame_config, on_not_found_attribute_callback=None):
        """To create API Events. event_name is an event alias. event_frame_config is a JSON which keys are keyword
         returned by the API at certain event, and values are an AsyncApiAssistant valid filter (aaa_filter_types.py).
         on_not_found_attribute_callback is a callback called if during a filter some keyword is not found in the
         returned values by the API. That callback can do whatever the user wants but must expect 1 argument which is
         the not found keyword"""
        is_defined_yet = self._event_filters.get(event_name, False)

        if not is_defined_yet:
            self._event_filters[event_name] = event_filter.EventFilter(event_name, event_frame_config,
                                                                       on_not_found_attribute_callback)
            return self._event_filters[event_name]
        else:
            raise Errors.AttempToOverwrite('event', event_name)

    async def run_event(self, event_name, data_frame):
        """When some values are recieved from API. In some processor node must be called this method must be called
        with the proper event_name and passing the values recieved"""
        triggers_list = self._event_filters[event_name].pass_filters(data_frame)
        for trigger in triggers_list:
            await self._node_types['trigger'][trigger](data_frame)

    @staticmethod
    async def http_request(request_type, kwargs={}):
        """This method purpose is being "request" part on the handler architecture. Just make HTTP request and return
        the response. request_type can be GET, POST, PUT and DELETE. kwargs are the params of http_request at
        ingest_ports.py"""
        request_function = ingest_ports.ingest_http_ports.get(request_type, _bad_petition_trigger)

        if request_function is _bad_petition_trigger:
            request_function(request_type)
        else:
            return await request_function(**kwargs)

    async def websocket_connection(self, websocket_name, url, preprocessor, on_connection=False):
        """create a websocket connection, hold the object into self._websockets dictionary with websocket_name keyword
        and stars the listening loop. Every messages recieved will be passed to preprocessor (or processor) and
        preform an on_connection function if is needed. on_connection function must expect 1 param which is the
        websocket itself (in case you could need send something, ws.send_str(str))"""
        websocket_exists_yet = self._websockets.get(websocket_name, False)

        if websocket_exists_yet:
            raise Errors.AttempToOverwrite('websocket', websocket_name)

        ws = await ingest_ports.websocket(url)
        self._websockets[websocket_name] = ws
        if on_connection:
            await on_connection(ws)
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await preprocessor(msg.data, ws)

    def get_websocket(self, websocket_name):
        return self._websockets[websocket_name]


"""    async def socket_conection(self, socket_name, url, port, preprocessor, on_conection=False):
        socket_exists_yet = self._sockets.get(socket_name, False)

        if socket_exists_yet:
            raise Errors.AttempToOverwrite('socket', socket_name)

        socket = await ingest_ports.socket(url, port)
        self._sockets[socket_name] = socket
        if on_conection:
            await on_conection(socket)
        async for msg in socket:
            await preprocessor(msg, socket)

    def get_socket(self, socket_name):
        return self._sockets[socket_name]
"""


def _missed_node(node_type, node_name):
    """Is an interface function if dict.get() not find a keyword"""
    raise Errors.MissedNode(node_type, node_name)


def _bad_petition_trigger(request_type):
    """Is an interface function if dict.get() not find a keyword"""
    raise Errors.BadHTTPPetition(request_type)
