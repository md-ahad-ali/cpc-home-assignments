class Building:

    def __init__(self, id, user_id, name, area_sqm):
        self.__id = id
        self.__user_id = user_id
        self.__name = name
        self.__area_sqm = area_sqm

    def get_building_details(self):
        return {
            "id": self.__id,
            "user_id": self.__user_id,
            "name": self.__name,
            "area_sqm": self.__area_sqm
        }

    def update_building(self, name, area_sqm):
        self.__name = name
        self.__area_sqm = area_sqm

    # Getters and Setters
    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name