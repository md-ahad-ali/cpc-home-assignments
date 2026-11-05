"""
Subsystem 2: Energy Data Management (FR2.1 - FR2.10)
Owner: S M Saifur Rahman

Classes: EnergyLog, CSVParser, ImportRecord
Each class has __init__, an initialize() method, and get/set methods.
"""

import csv
import os
from datetime import datetime


class EnergyLog:
    MAX_KWH = 10000.0
    MIN_TEMP = -30.0
    MAX_TEMP = 60.0

    def __init__(self, log_id, room_id, timestamp, energy_consumed_kwh, indoor_temp):
        self._id = log_id
        self._room_id = room_id
        self._timestamp = None
        self._energy_consumed_kwh = 0.0
        self._indoor_temp = 0.0
        self.initialize()
        self.set_timestamp(timestamp)
        self.set_energy_consumed_kwh(energy_consumed_kwh)
        self.set_indoor_temp(indoor_temp)

    def initialize(self):
        """Clear the fields before the setters fill them."""
        self._timestamp = None
        self._energy_consumed_kwh = 0.0
        self._indoor_temp = 0.0

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_room_id(self):
        return self._room_id

    def get_timestamp(self):
        return self._timestamp

    def get_energy_consumed_kwh(self):
        return self._energy_consumed_kwh

    def get_indoor_temp(self):
        return self._indoor_temp

    # ---- setters (FR2.3: range checks) ----
    def set_timestamp(self, timestamp):
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be a datetime")
        self._timestamp = timestamp

    def set_energy_consumed_kwh(self, value):
        value = float(value)
        if value < 0 or value > EnergyLog.MAX_KWH:
            raise ValueError("kWh must be between 0 and " + str(EnergyLog.MAX_KWH))
        self._energy_consumed_kwh = value

    def set_indoor_temp(self, value):
        value = float(value)
        if value < EnergyLog.MIN_TEMP or value > EnergyLog.MAX_TEMP:
            raise ValueError("temperature is out of range")
        self._indoor_temp = value

    def to_dict(self):
        return {
            "id": self._id,
            "room_id": self._room_id,
            "timestamp": self._timestamp,
            "energy_consumed_kwh": self._energy_consumed_kwh,
            "indoor_temp": self._indoor_temp,
        }


class CSVParser:
    REQUIRED_COLUMNS = ("room_id", "timestamp", "energy_consumed_kwh", "indoor_temp")

    def __init__(self, file_path, max_size_mb=50):
        self._file_path = ""
        self._max_size_mb = 50
        self._errors = []
        self._seen_keys = set()
        self.initialize()
        self.set_file_path(file_path)
        self.set_max_size_mb(max_size_mb)

    def initialize(self):
        """Clear errors and the duplicate memory before a new import."""
        self._errors = []
        self._seen_keys = set()

    # ---- getters ----
    def get_file_path(self):
        return self._file_path

    def get_max_size_mb(self):
        return self._max_size_mb

    def get_errors(self):
        return list(self._errors)

    # ---- setters ----
    def set_file_path(self, file_path):
        self._file_path = file_path

    def set_max_size_mb(self, value):
        if value <= 0:
            raise ValueError("max_size_mb must be above zero")
        self._max_size_mb = value

    # ---- behavior ----
    def validate_csv(self):
        """FR2.2: check the file type, the size and the header."""
        if not self._file_path.lower().endswith(".csv"):
            raise ValueError("only .csv files are allowed")
        if not os.path.isfile(self._file_path):
            raise ValueError("file not found")
        size_mb = os.path.getsize(self._file_path) / (1024 * 1024)
        if size_mb > self._max_size_mb:
            raise ValueError("file is too large")
        with open(self._file_path, newline="") as f:
            header = next(csv.reader(f), [])
        missing = [c for c in CSVParser.REQUIRED_COLUMNS if c not in header]
        if missing:
            raise ValueError("missing columns: " + ", ".join(missing))
        return True

    def parse_data(self, valid_room_ids):
        """Return the valid EnergyLog objects. Bad rows go to the error list."""
        self.initialize()
        self.validate_csv()
        logs = []
        with open(self._file_path, newline="") as f:
            for line_no, row in enumerate(csv.DictReader(f), start=2):
                try:
                    room_id = int(row["room_id"])
                    if room_id not in valid_room_ids:  # FR2.6
                        raise ValueError("unknown room " + str(room_id))
                    stamp = datetime.fromisoformat(row["timestamp"])
                    key = (room_id, stamp)
                    if key in self._seen_keys:  # FR2.5
                        continue
                    log = EnergyLog(
                        None, room_id, stamp,
                        row["energy_consumed_kwh"], row["indoor_temp"],
                    )
                    self._seen_keys.add(key)
                    logs.append(log)
                except (ValueError, KeyError) as error:  # FR2.4
                    self._errors.append("line " + str(line_no) + ": " + str(error))
        return logs


class ImportRecord:
    def __init__(self, record_id, user_id, file_name):
        self._id = record_id
        self._user_id = user_id
        self._file_name = file_name
        self._rows_imported = 0
        self._rows_rejected = 0
        self._status = "pending"
        self._created_at = None
        self.initialize()

    def initialize(self):
        self._created_at = datetime.now()
        self._status = "pending"

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_user_id(self):
        return self._user_id

    def get_file_name(self):
        return self._file_name

    def get_rows_imported(self):
        return self._rows_imported

    def get_rows_rejected(self):
        return self._rows_rejected

    def get_status(self):
        return self._status

    def get_created_at(self):
        return self._created_at

    # ---- setters ----
    def set_rows_imported(self, value):
        if value < 0:
            raise ValueError("rows_imported must not be negative")
        self._rows_imported = value

    def set_rows_rejected(self, value):
        if value < 0:
            raise ValueError("rows_rejected must not be negative")
        self._rows_rejected = value

    def set_status(self, status):
        if status not in ("pending", "success", "rolled_back"):
            raise ValueError("invalid status")
        self._status = status

    def finish(self, imported, rejected, strict=True):
        """FR2.10: in strict mode any bad row rolls back the whole import."""
        self.set_rows_rejected(rejected)
        if strict and rejected > 0:
            self.set_rows_imported(0)
            self.set_status("rolled_back")
        else:
            self.set_rows_imported(imported)
            self.set_status("success")


if __name__ == "__main__":
    import tempfile

    path = os.path.join(tempfile.gettempdir(), "demo_energy.csv")
    with open(path, "w") as f:
        f.write("room_id,timestamp,energy_consumed_kwh,indoor_temp\n")
        f.write("1,2026-10-01 08:00,5.2,21.0\n")
        f.write("1,2026-10-01 08:00,5.2,21.0\n")   # duplicate
        f.write("9,2026-10-01 09:00,4.0,20.5\n")   # unknown room
        f.write("1,2026-10-01 10:00,-3,20.5\n")    # bad value

    parser = CSVParser(path)
    logs = parser.parse_data(valid_room_ids={1, 2})
    record = ImportRecord(1, 1, "demo_energy.csv")
    record.finish(len(logs), len(parser.get_errors()), strict=False)
    print("Imported:", len(logs), "Errors:", parser.get_errors())
    print("Status:", record.get_status())
