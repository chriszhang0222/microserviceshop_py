

class ConfigCenter:
    def __init__(self, *args, **kwargs):
        pass

    def __pull(self, id):
        raise NotImplementedError

    def __push(self, id):
        raise NotImplementedError
