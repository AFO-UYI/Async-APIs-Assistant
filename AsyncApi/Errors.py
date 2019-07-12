class BadNodeType(Exception):
    def __init__(self, node_type):
        super(BadNodeType, self).__init__(f'The node type you are trying to define ("{node_type}") not exist.')


class MissedNode(Exception):
    def __init__(self, node_type, node_name):
        super(MissedNode, self).__init__(f'You are asking for a {node_type} named "{node_name}". '
                                         f'But you not defined it')


class AttempToOverwrite(Exception):
    def __init__(self, item_type, item_name, event_name=False):
        super(AttempToOverwrite, self).__init__(f'You are trying to overwrite the {item_name} {item_type}' +
                                                (f' on {event_name} event.' if event_name else '.'))


class BadHTTPPetition(Exception):
    def __init__(self, request_type):
        super(BadHTTPPetition, self).__init__(f'You attemp to make a "{request_type}" request. '
                                              f'This request type not exist or is not implemented yet')
