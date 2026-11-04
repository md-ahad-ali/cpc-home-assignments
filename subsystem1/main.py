"""
Subsystem 1: User & Building Management (FR1.1 - FR1.10)
Owner: Thi Ha Vu
"""

from user import User
from building import Building
from room import Room

if __name__ == "__main__":
    users = []
    admin = User(1, "thi", "secret123", "Admin")
    admin.register(users)
    print("Login ok:", admin.login("secret123"))

    b = Building(1, admin.get_id(), "Main Hall", 1200)
    b.add_room(Room(1, 1, "Lab 101"))
    b.add_room(Room(2, 1, "Office 2"))
    print("Search 'lab':", [r.get_room_name() for r in b.search_rooms("lab")])
