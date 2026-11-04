class Room:

    def __init__(self, id, building_id, occupant_id, room_name):
        self.__id = id
        self.__building_id = building_id
        self.__occupant_id = occupant_id
        self.__room_name = room_name

    def get_room_details(self):
        return {
            "id": self.__id,
            "building_id": self.__building_id,
            "occupant_id": self.__occupant_id,
            "room_name": self.__room_name
        }

    def assign_occupant(self, occupant_id):
        self.__occupant_id = occupant_id

    # Getters and Setters
    def get_room_name(self):
        return self.__room_name

    def set_room_name(self, room_name):
        self.__room_name = room_name