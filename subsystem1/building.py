"""
Subsystem 1: User & Building Management (FR1.1 - FR1.10)
Owner: Thi Ha Vu
"""


class Building:
    def __init__(self, building_id, user_id, name, area_sqm):
        self._id = building_id
        self._user_id = user_id
        self._name = ""
        self._area_sqm = 0.0
        self._rooms = []
        self.initialize()
        self.set_name(name)
        self.set_area_sqm(area_sqm)

    def initialize(self):
        self._rooms = []

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_user_id(self):
        return self._user_id

    def get_name(self):
        return self._name

    def get_area_sqm(self):
        return self._area_sqm

    def get_rooms(self):
        return list(self._rooms)

    # ---- setters ----
    def set_name(self, name):
        if not name or not name.strip():
            raise ValueError("building name must not be empty")
        self._name = name.strip()

    def set_area_sqm(self, area_sqm):
        if area_sqm <= 0:
            raise ValueError("area_sqm must be above zero")
        self._area_sqm = float(area_sqm)

    # ---- behavior ----
    def add_room(self, room):
        """FR1.9: link a room to this building."""
        if room.get_building_id() != self._id:
            raise ValueError("room belongs to another building")
        self._rooms.append(room)

    def remove_room(self, room_id):
        """Cascade rule: the room leaves the building."""
        self._rooms = [r for r in self._rooms if r.get_id() != room_id]

    def search_rooms(self, text):
        """FR1.10: find rooms by part of the name."""
        text = text.lower()
        return [r for r in self._rooms if text in r.get_room_name().lower()]
