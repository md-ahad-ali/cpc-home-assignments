"""Custom exception hierarchy, one base class per subsystem.

Each subsystem (database, users, buildings, rooms, energy logs) gets its
own error class so a Flask error handler can map it to the right HTTP
status code and a consistent JSON body: {"error": "<message>"}.
"""


class AppError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def to_dict(self):
        return {"error": self.message}


class DatabaseError(AppError):
    status_code = 503


class DatabaseConnectionError(DatabaseError):
    status_code = 503


class UserError(AppError):
    status_code = 400


class UserNotFoundError(UserError):
    status_code = 404


class BuildingError(AppError):
    status_code = 400


class InvalidBuildingIdError(BuildingError):
    status_code = 400


class BuildingNotFoundError(BuildingError):
    status_code = 404


class RoomError(AppError):
    status_code = 400


class InvalidRoomIdError(RoomError):
    status_code = 400


class RoomNotFoundError(RoomError):
    status_code = 404


class EnergyLogError(AppError):
    status_code = 400


class InvalidEnergyLogRoomIdError(EnergyLogError):
    status_code = 400
