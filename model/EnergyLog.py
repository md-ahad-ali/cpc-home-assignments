from datetime import datetime


class EnergyLog:

    def __init__(self, id, room_id, timestamp, energy_consumed_kwh, indoor_temp):
        self.__id = id
        self.__room_id = room_id
        self.__timestamp = timestamp
        self.__energy_consumed_kwh = energy_consumed_kwh
        self.__indoor_temp = indoor_temp

    def get_energy_details(self):
        return {
            "id": self.__id,
            "room_id": self.__room_id,
            "timestamp": self.__timestamp,
            "energy_consumed_kwh": self.__energy_consumed_kwh,
            "indoor_temp": self.__indoor_temp
        }

    def update_energy_consumption(self, energy_consumed_kwh):
        self.__energy_consumed_kwh = energy_consumed_kwh

    # Getters and Setters
    def get_energy_consumed(self):
        return self.__energy_consumed_kwh

    def set_energy_consumed(self, energy_consumed_kwh):
        self.__energy_consumed_kwh = energy_consumed_kwh