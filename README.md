Async APIs Assistant

A Python library to organise and make easier API handlings.

# Sketching the idea

The idea is isolate some part of API handling. Encapsulating those parts more attached to API design separately to parts more close to clients needs.

A design to solve the need for separate parts have 4 types of parts, distributed on a general API handlings workflow.

![API Handling diagram](https://raw.githubusercontent.com/AFO-UYI/Async-APIs-Assistant/develop/readme_img/diagram%20api%20handler.png)

Inputs, parsers and a half of event filters are totally attached to APIs design. The other half of event filters and triggers are client needs side.

Async APIs Assistant gives tools to compose the API side being as respectful to SOLID principle as posible, writing in a single file one time only all the inputs, parsers and events, and this is really important considering that an API handler must be maintained often each time the API is updated.

On the other hand, for the client side parts, events filters and triggers can be configured with a JSON with proper keywords-values. So its really dynamic and accesible to changes. (Explicit functions that expects those json to configure filters and triggers are pending to implement. Will be implemented when Cython investigation finish).

Inputs can be http request, websockets or plain sockets (a.k.a. ingest ports) (plain sockets are pending to implement because AsyncIO raise some errors when attempt a connection with `open_connection()`. There are a few alternatives being studied to implement the alternative that fits better.)

Parsers can be pre-processors and processors. The purpose is just convert input messages into usable python dictionaries. Processors is the part that really convert messages. Pre-processors purpose is, in case of have an ingest port that return diferents types of messages, a pre-processor makes a minimal analisis to chose which processor must to be used.

Event filters consists in define the filters needs for each data type holded by a data frame (a.k.a. an API message converted into a dictionary). Eg: maybe a data frame holds a number as value for the key 'age' and a trigger must be called if that age is between certain numbers. Then you must instance an Event filter with a `CuantityRange` filter object attached to 'age' keyword . The proper event filter must be called at the end of processors with `your_api_handler.run_event('event_you_want', data_frame)`, but this could change.

Triggers are just the behaviour you want to preform if a recieved data frame fulfills event filters. After define the trigger function you must to add it into an event filter with the trigger name and filter conditions. Eg: you did a trigger named 'mid_age', and wants call it if the age keyword in a data frame is between 20 and 40. You add it to event filter you wants as follows `event_you_want.add_trigger_filter('mid_age', {'age': {'being': 'between', 'values': [20, 40]}})`.

# Usage

### Async API Assistant Core

First of all, you must need instance a new API handler object. `your_api_handler = AsyncApi.create_api_handler()`

To define a part you must use `define_node()` decorator as follows:
```python
@your_api_handler.define_node(part_name [, alias])
async def your_own_function():
    pass
```

The `part_name` is a string that can be `ingest_port`, `pre_processor`, `processor`, `request` and `trigger`. An optional `alias` will overwrite the function name. After definition, the function body will be holded in the api handler object. Call directly that function will return `None`. Indeed, you can delete that name after defined it with `del your_own_function`.

To get and call that function (will change):
```python
your_api_handler.get_[part_name](function_name_or_alias)                 # returns a reference of the function

your_api_handler.get_[part_name](function_name_or_alias)(function_args)  # runs the function
```

To define an event: `your_api_handler.define_event(event_name, event_filters_config [, on_not_found_attribute_callback]):`.
`event_name` is just a string to reference that event, `event_filters_config` is a dictinary with data frame keywords as keywords and instanced filter objects as values. An optional `on_not_found_attribute_callback` is a function that expect as param the keyword missed to preform what you wants if some keyword in the event object was not found in a recieved data frame. This function returns a `EventFilter` object. Eg: `my_new_event = your_api_handler.define_event('on_msg_recieved', {'age': AsyncApi.CuantityRange()})`

To run event filters: `await your_api_handler.run_event('event_name_you_want', data_frame)`.

To make a HTTP request: `await http_request(request_type, request_config)`
`request_type` is a string: `GET`, `POST`, `PUT` and `DELETE`.
`request_config` is a dictionary with all the needed info to run a request. The keywords can be:
 * `url`: just the url for the request.
 * `is_a_json_returned`: a boolean. If True return the response as a dictionary. Otherwise return it as string.
 * `headers`: a dictionary. Keyword must be headers name such as `content-type` and values are headers values like `application/json`.
 * `data`: a string that will be the request body.
 * `json`: if you request send a json. You can use this param with a dictionary. Automatically will be setted even headers.
 * `params`: a dictionary to build GET params at url. Eg: 
 `{'url': 'someurl.com', 'params': {'key1': 'value1', 'key2': 'value2'}} => someurl.com?key1=value1&key2=value2`
 
To make a websocket: `await twitch_api.websocket_connection(websocket_name, url, pre-processor, on_connection_callback)`
`websocket_name` is a string used as alias to reference to it. `url` is just a string with the url to connect the websocket. `pre-processor` is a parser reference (pre-processor or processor) which will parse recieved messages. `on_connection_callback` is a function to preform something before entry on the listening loop. The function must expect the websocket as param, just in case you could need send message. To send message with the websocket directly you must call `websocket.send_str(message)`. `message` doesnt need to be encoded to bytes.

To get a websocket reference: `your_api_handler.get_websocket(websocket_name_you_want)`.

To shutdown the API Handler: `your_api_handler.shutdown()`. This will close websockets and sockets connections.

---

### Event Filters configuration

When you call `define_event()`, the method returns an `EventFilter` object with that object you can configure the filter you want for each data type in a data frame.

To define filter config for a trigger: `your_event_object.add_trigger_filter(trigger_name, filter_specification_dict)`.
`trigger_name` is a string. The name of the trigger you want to be called if fullfils the config you are adding. `filter_specification_dict` is dictionary where keywords are the keywords expected on a data frame, the same keywords that you pass at event definition, values are a valid filter configuration for the filter object attached to certain keyword. You can omit some keywords if you dont need a filter active in those keywords.

After configure all the triggers filters attached to an event, you must seal the event calling `your_event_object.seal_event_filters()`.

---

### Filter Objects

##### AsyncApi.CuantityRange:

Given a number, returns True only if the number fits in a range assigned to the trigger filter.

The configuration value for this filter is dictionary with the comparison needed as value for 'being' keyword and a number o list of two numbers as value for 'values' keyword. Integer numbers will be casted to floats automatically.

Those comparisons can be:
* `equal` with keyword 'value' as `X`
* `greater` with keyword 'value' as `X`
* `lower` with keyword 'value' as `X`
* `between` with keyword 'value' as `[X, Y]`

Eg: `your_event_object.add_trigger_filter('mid_age', {'age', {'being': 'between', 'values': [20, 40]}})`

##### AsyncApi.HardBoolString:

BoolSrings (maybe I must consider another name) are a non negative integer interpreted as a list of booleans.

Eg: `140 = 0b10001100 = [True, False, False, False, True, True, False, False]`

This filter returns True only if a data frame matches all True indexes.

The configuration value for this filter is just a non negative integer. Floats are not valid.

##### AsyncApi.SoftBoolString:

Is the same as `HardBoolString`, but return True if matches at least one True index.

# TO-DOs

Must to be implemented Sockets and much more variety of FilterObjects. But at this moment, Async Api Assistant is a bit paused due to investigation about Cython and how much benefits can give mixin Cython and AsyncIO to this library.

