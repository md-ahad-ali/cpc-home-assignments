from processors.base_processor import BaseProcessor


class MeterFilter(BaseProcessor):

    def process(self, event):
        if not event.active:
            return None
        if event.power < 0.5:
            return None
        return event