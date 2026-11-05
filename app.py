import pymysql
from flask import Flask, jsonify

from db import get_connection
from errors import (
    AppError,
    BuildingNotFoundError,
    DatabaseConnectionError,
    InvalidBuildingIdError,
    InvalidEnergyLogRoomIdError,
    RoomNotFoundError,
)

app = Flask(__name__)


def run_query(query, params=None):
    """Open a connection, run one query, and always close the connection.

    Any MySQL failure (connection or query) is converted into a
    DatabaseConnectionError so routes don't need their own try/except.
    """
    try:
        connection = get_connection()
    except pymysql.MySQLError as exc:
        raise DatabaseConnectionError(f"Could not connect to the database: {exc}") from exc

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except pymysql.MySQLError as exc:
        raise DatabaseConnectionError(f"Database query failed: {exc}") from exc
    finally:
        connection.close()


@app.errorhandler(AppError)
def handle_app_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify(error="Resource not found"), 404


@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify(error="Internal server error"), 500


@app.route("/")
def home():
    return jsonify(message="Flask + MySQL intro app is running (ecopulse schema)")


@app.route("/users", methods=["GET"])
def list_users():
    users = run_query("SELECT id, username, role FROM users")
    return jsonify(users)


@app.route("/buildings", methods=["GET"])
def list_buildings():
    buildings = run_query("SELECT id, user_id, name, area_sqm FROM buildings")
    return jsonify(buildings)


@app.route("/buildings/<int:building_id>/rooms", methods=["GET"])
def list_rooms(building_id):
    if building_id <= 0:
        raise InvalidBuildingIdError(f"Building id must be a positive integer, got {building_id}")

    building = run_query("SELECT id FROM buildings WHERE id = %s", (building_id,))
    if not building:
        raise BuildingNotFoundError(f"Building {building_id} not found")

    rooms = run_query(
        "SELECT id, building_id, occupant_id, room_name FROM rooms WHERE building_id = %s",
        (building_id,),
    )
    return jsonify(rooms)


@app.route("/rooms/<int:room_id>/energy-logs", methods=["GET"])
def list_energy_logs(room_id):
    if room_id <= 0:
        raise InvalidEnergyLogRoomIdError(f"Room id must be a positive integer, got {room_id}")

    room = run_query("SELECT id FROM rooms WHERE id = %s", (room_id,))
    if not room:
        raise RoomNotFoundError(f"Room {room_id} not found")

    logs = run_query(
        """
        SELECT id, room_id, `timestamp`, energy_consumed_kwh, indoor_temp
        FROM energy_logs
        WHERE room_id = %s
        ORDER BY `timestamp`
        LIMIT 100
        """,
        (room_id,),
    )
    return jsonify(logs)


if __name__ == "__main__":
    app.run(debug=True)
