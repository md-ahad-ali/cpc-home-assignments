class EnergyEvent:

    def __init__(self, meter_id, power, active):
        self.meter_id = meter_id
        self.power = power
        self.active = active
        self.carbon = 0