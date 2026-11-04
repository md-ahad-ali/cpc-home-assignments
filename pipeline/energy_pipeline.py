class EnergyPipeline:

    def __init__(self, processors=None):
        self.processors = processors or []

    def __or__(self, processor):
        return EnergyPipeline(
            self.processors + [processor]
        )

    def process(self, event):
        for processor in self.processors:
            event = processor.process(event)
            if event is None:
                return None
        return event