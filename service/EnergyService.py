
class EnergyService:

    def __init__(self, tariff=0.30, co2_factor=0.40):
        self.__tariff = tariff
        self.__co2_factor = co2_factor
        self.__energy_logs = []

    # Method 1: Add energy record
    def add_energy_log(self, energy_log):
        self.__energy_logs.append(energy_log)

    # Method 2: Calculate energy summary
    def calculate_summary(self):
        total_kwh = sum(
            log.get_energy_consumed()
            for log in self.__energy_logs
        )

        return {
            "total_kwh": round(total_kwh, 2),
            "cost_eur": round(total_kwh * self.__tariff, 2),
            "carbon_kg_co2": round(
                total_kwh * self.__co2_factor, 2
            )
        }

    # Getters and Setters
    def get_tariff(self):
        return self.__tariff

    def set_tariff(self, tariff):
        self.__tariff = tariff

    def get_energy_logs(self):
        return self.__energy_logs
