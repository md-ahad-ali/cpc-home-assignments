import pandas as pd
from datetime import datetime
import time

class EnergyLog:
    def __init__(self, id, room_id, timestamp, energy_consumed_kwh, indoor_temp):
        self.__id = id
        self.__room_id = room_id
        self.__timestamp = timestamp
        self.__energy_consumed_kwh = energy_consumed_kwh
        self.__indoor_temp = indoor_temp

    # Getters
    def get_id(self):
        return self.__id

    def get_room_id(self):
        return self.__room_id

    def get_timestamp(self):
        return self.__timestamp

    def get_energy_consumed(self):
        return self.__energy_consumed_kwh

    def get_indoor_temp(self):
        return self.__indoor_temp

    # Setters
    def set_id(self, id):
        self.__id = id

    def set_room_id(self, room_id):
        self.__room_id = room_id

    def set_timestamp(self, timestamp):
        self.__timestamp = timestamp

    def set_energy_consumed(self, energy_consumed_kwh):
        self.__energy_consumed_kwh = energy_consumed_kwh

    def set_indoor_temp(self, indoor_temp):
        self.__indoor_temp = indoor_temp

    # Utility method
    def get_energy_details(self):
        return {
            "id": self.__id,
            "room_id": self.__room_id,
            "timestamp": self.__timestamp,
            "energy_consumed_kwh": self.__energy_consumed_kwh,
            "indoor_temp": self.__indoor_temp
        }