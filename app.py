from flask import Flask, jsonify

from db import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(message="Flask + MySQL intro app is running (ecopulse schema)")


@app.route("/users", methods=["GET"])
def list_users():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
    finally:
        connection.close()
    return jsonify(users)


@app.route("/buildings", methods=["GET"])
def list_buildings():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, user_id, name, area_sqm FROM buildings")
            buildings = cursor.fetchall()
    finally:
        connection.close()
    return jsonify(buildings)


@app.route("/buildings/<int:building_id>/rooms", methods=["GET"])
def list_rooms(building_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, building_id, occupant_id, room_name FROM rooms WHERE building_id = %s",
                (building_id,),
            )
            rooms = cursor.fetchall()
    finally:
        connection.close()
    return jsonify(rooms)


@app.route("/rooms/<int:room_id>/energy-logs", methods=["GET"])
def list_energy_logs(room_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, room_id, `timestamp`, energy_consumed_kwh, indoor_temp
                FROM energy_logs
                WHERE room_id = %s
                ORDER BY `timestamp`
                LIMIT 100
                """,
                (room_id,),
            )
            logs = cursor.fetchall()
    finally:
        connection.close()
    return jsonify(logs)


if __name__ == "__main__":
    app.run(debug=True)
