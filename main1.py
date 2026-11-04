from datetime import datetime

from model.EnergyLog import EnergyLog
from service.EnergyService import EnergyService


def main():

    service = EnergyService(tariff=0.30, co2_factor=0.40)

    log1 = EnergyLog(1, 101, datetime.now(), 15.5, 22.5)
    log2 = EnergyLog(2, 101, datetime.now(), 20.0, 23.0)
    log3 = EnergyLog(3, 102, datetime.now(), 10.5, 21.0)

    service.add_energy_log(log1)
    service.add_energy_log(log2)
    service.add_energy_log(log3)

    print("Energy Summary:")
    print(service.calculate_summary())


if __name__ == "__main__":
    main()