"""
Subsystem 1: User & Building Management (FR1.1 - FR1.10)
Owner: Thi Ha Vu
"""


class Room:
    def __init__(self, room_id, building_id, room_name):
        self._id = room_id
        self._building_id = building_id
        self._room_name = ""
        self.initialize()
        self.set_room_name(room_name)

    def initialize(self):
        pass

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_building_id(self):
        return self._building_id

    def get_room_name(self):
        return self._room_name

    # ---- setters ----
    def set_room_name(self, room_name):
        if not room_name or not room_name.strip():
            raise ValueError("room name must not be empty")
        self._room_name = room_name.strip()

    def set_building_id(self, building_id):
        self._building_id = building_id
