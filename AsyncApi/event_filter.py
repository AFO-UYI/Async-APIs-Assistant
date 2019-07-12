"""Here is where triggers filters are defined and holded with a trigger name attached to call it if
filters are passed"""


import numpy as np

import AsyncApi.Errors as Errors


class EventFilter:
    """An event object holds a event name for exceptions raised, an attribute dictionary with keywords expected on that
    event and filter objects attached to those keywords and a callback to preform whatever in case of not found
    on dataframe an expected keyword"""
    def __init__(self, event_name, attributes_dict, on_not_found_attribute_callback=None):
        self.event_name = event_name
        self._triggers_name_list = []
        self._attribtutes_objects = attributes_dict
        self.on_not_found_attribute_callback = on_not_found_attribute_callback

    def add_trigger_filter(self, trigger_name, filter_specification_dict):
        """hold the trigger name and add filters for the kaywords passed on the filter_specification_dict.
        If a keyword on the event is not passed in the specification an empty filter will be configured
         for missed keywords"""
        if trigger_name in self._triggers_name_list:
            raise Errors.AttempToOverwrite('trigger', trigger_name, self.event_name)
        else:
            self._triggers_name_list.append(trigger_name)
            for key_attribute, filter_object in self._attribtutes_objects.items():
                attribute_filter_config = filter_specification_dict.get(key_attribute, None)
                if attribute_filter_config:
                    filter_object.add_filter(attribute_filter_config)
                else:
                    filter_object.add_empty_cell()

    def seal_event_filters(self):
        """seal all the filters"""
        for _, filter_object in self._attribtutes_objects.items():
            filter_object.seal_filter()

    def pass_filters(self, data_frame):
        """ask for which triggers must be called for certain data_frame. returns a list with all the triggers names
        that pass all filters. If the data frame hasnt an expected keyword, return an empty list without triggers names
        and preform the on_not_founf_attribute_callback if that callback was passed."""

        control_array = np.ones(len(self._triggers_name_list), dtype=np.bool)

        for attribute_name, filter_object in self._attribtutes_objects.items():
            data_frame_attribute = data_frame.get(attribute_name, False)

            if not data_frame_attribute:
                if self.on_not_found_attribute_callback:
                    self.on_not_found_attribute_callback(attribute_name)
                return []

            np.multiply(control_array, filter_object.filter(data_frame_attribute), control_array)

        return [self._triggers_name_list[index] for index in np.where(control_array)[0]]
