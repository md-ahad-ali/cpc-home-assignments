class EventStream:

    def __init__(self, events):
        self.events = iter(events)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.events)