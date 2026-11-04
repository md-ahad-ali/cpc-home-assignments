from models.energy_event import EnergyEvent

from processors.meter_filter import MeterFilter
from processors.carbon_transformer import CarbonTransformer

from pipeline.energy_pipeline import EnergyPipeline
from streams.event_stream import EventStream

events = [
    EnergyEvent("M001", 5.5, True),
    EnergyEvent("M002", 0.2, True),
    EnergyEvent("M003", 3.0, False),
    EnergyEvent("M004", 8.0, True)
]

pipeline = (
    EnergyPipeline()
    | MeterFilter()
    | CarbonTransformer()
)
stream = EventStream(events)
for event in stream:
    result = pipeline.process(event)
    if result is not None:
        print(
            f"Meter: {result.meter_id}, "
            f"Power: {result.power} kW, "
            f"Carbon: {result.carbon} kg CO2"
        )