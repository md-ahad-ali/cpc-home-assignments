from processors.base_processor import BaseProcessor


class CarbonTransformer(BaseProcessor):

    def process(self, event):
        carbon_factor = 0.35
        hours = 1
        event.carbon = event.power * hours * carbon_factor
        return event