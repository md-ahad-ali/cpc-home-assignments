import pandas as pd
import time

class CSVParser:
    def __init__(self, file_path):
        self.__file_path = file_path
        self.__raw_data = None
        self.__cleaned_data = None

    def get_file_path(self):
        return self.__file_path

    def set_file_path(self, file_path):
        self.__file_path = file_path

    def initialize_parser(self):
        self.__raw_data = pd.read_csv(self.__file_path)

    def validate_csv(self):
        self.initialize_parser()
        required_cols = ["room_id", "timestamp", "energy_consumed_kwh", "indoor_temp"]
        for col in required_cols:
            if col not in self.__raw_data.columns:
                return False
        self.__cleaned_data = self.__raw_data.dropna(subset=required_cols)
        return True

    def parse_data(self):
        if self.__cleaned_data is None:
            self.validate_csv()
        
        deduplicated = self.__cleaned_data.drop_duplicates(subset=["room_id", "timestamp"])
        logs = []
        for _, row in deduplicated.iterrows():
            log = EnergyLog(
                id=0,
                room_id=int(row["room_id"]),
                timestamp=str(row["timestamp"]),
                energy_consumed_kwh=float(row["energy_consumed_kwh"]),
                indoor_temp=float(row["indoor_temp"])
            )
            logs.append(log)
        return logs


