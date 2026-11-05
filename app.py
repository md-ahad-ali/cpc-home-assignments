import os
import statistics
from datetime import date, timedelta

import pymysql
from flask import Flask, jsonify, request

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

TARIFF_EUR_PER_KWH = float(os.getenv("TARIFF_EUR_PER_KWH", "0.30"))
EMISSION_KG_PER_KWH = float(os.getenv("EMISSION_KG_PER_KWH", "0.40"))
# Benchmark for the sustainability score, in kWh per square metre per year.
BENCHMARK_KWH_PER_SQM_YEAR = float(os.getenv("BENCHMARK_KWH_PER_SQM_YEAR", "100"))


class InvalidParameterError(AppError):
    """Bad query parameter. Assumes AppError(message) and a status_code attribute."""
    status_code = 400


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


# ------------------------------------------------- analytics helpers


def _num(value):
    """NFR3.5: round to two decimals and convert Decimal to float."""
    return round(float(value or 0), 2)


def _cost(kwh):
    return _num(float(kwh or 0) * TARIFF_EUR_PER_KWH)


def _carbon(kwh):
    return _num(float(kwh or 0) * EMISSION_KG_PER_KWH)


def _parse_date(name):
    raw = request.args.get(name)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise InvalidParameterError(f"'{name}' must use the format YYYY-MM-DD, got '{raw}'")


def _range_sql():
    """Return (sql, params) with AND clauses on el.timestamp for start and end."""
    start, end = _parse_date("start"), _parse_date("end")
    if start and end and start > end:
        raise InvalidParameterError("'start' must not be after 'end'")

    sql, params = "", []
    if start:
        sql += " AND el.`timestamp` >= %s"
        params.append(start)
    if end:
        sql += " AND el.`timestamp` < %s"  # end is inclusive, so use the next day
        params.append(end + timedelta(days=1))
    return sql, params


def _int_arg(name, default, minimum, maximum):
    raw = request.args.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise InvalidParameterError(f"'{name}' must be an integer, got '{raw}'")
    if not minimum <= value <= maximum:
        raise InvalidParameterError(f"'{name}' must be between {minimum} and {maximum}")
    return value


def _get_building(building_id):
    if building_id <= 0:
        raise InvalidBuildingIdError(f"Building id must be a positive integer, got {building_id}")
    rows = run_query("SELECT id, name, area_sqm FROM buildings WHERE id = %s", (building_id,))
    if not rows:
        raise BuildingNotFoundError(f"Building {building_id} not found")
    return rows[0]


def _get_room(room_id):
    if room_id <= 0:
        raise InvalidEnergyLogRoomIdError(f"Room id must be a positive integer, got {room_id}")
    rows = run_query("SELECT id, building_id, room_name FROM rooms WHERE id = %s", (room_id,))
    if not rows:
        raise RoomNotFoundError(f"Room {room_id} not found")
    return rows[0]


def _sustainability_score(total_kwh, area_sqm, days):
    """Score from 0 to 100. 100 means at or below the benchmark intensity.

    intensity = kWh per m2 in the period
    benchmark = BENCHMARK_KWH_PER_SQM_YEAR scaled to the period length
    score     = min(100, 100 * benchmark / intensity)
    """
    area = float(area_sqm or 0)
    if area <= 0:
        return None, None
    intensity = float(total_kwh or 0) / area
    benchmark = BENCHMARK_KWH_PER_SQM_YEAR * max(days, 1) / 365
    if intensity <= 0:
        return 100.0, 0.0
    return _num(min(100.0, 100.0 * benchmark / intensity)), _num(intensity)


# ------------------------------------------------------ existing routes


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




@app.route("/analytics/dashboard", methods=["GET"])  # FR3.1, FR3.6
def analytics_dashboard():
    range_sql, range_params = _range_sql()
    rows = run_query(
        f"""
        SELECT b.id, b.name, b.area_sqm,
               COALESCE(SUM(el.energy_consumed_kwh), 0) AS total_kwh,
               MIN(el.`timestamp`) AS first_log,
               MAX(el.`timestamp`) AS last_log
        FROM buildings b
        LEFT JOIN rooms r ON r.building_id = b.id
        LEFT JOIN energy_logs el ON el.room_id = r.id {range_sql}
        GROUP BY b.id, b.name, b.area_sqm
        ORDER BY b.id
        """,
        tuple(range_params),
    )

    buildings, grand_kwh = [], 0.0
    for row in rows:
        kwh = float(row["total_kwh"])
        grand_kwh += kwh
        days = (row["last_log"] - row["first_log"]).days + 1 if row["first_log"] else 1
        score, _ = _sustainability_score(kwh, row["area_sqm"], days)
        buildings.append(
            {
                "building_id": row["id"],
                "name": row["name"],
                "total_kwh": _num(kwh),
                "cost_eur": _cost(kwh),
                "carbon_kg_co2": _carbon(kwh),
                "sustainability_score": score,
            }
        )

    return jsonify(
        totals={
            "total_kwh": _num(grand_kwh),
            "cost_eur": _cost(grand_kwh),
            "carbon_kg_co2": _carbon(grand_kwh),
        },
        buildings=buildings,
    )


@app.route("/analytics/buildings/<int:building_id>/summary", methods=["GET"])  # FR3.2, FR3.3
def analytics_building_summary(building_id):
    building = _get_building(building_id)
    range_sql, range_params = _range_sql()
    row = run_query(
        f"""
        SELECT COALESCE(SUM(el.energy_consumed_kwh), 0) AS total_kwh,
               AVG(el.energy_consumed_kwh) AS avg_kwh,
               AVG(el.indoor_temp) AS avg_temp,
               COUNT(el.id) AS log_count
        FROM energy_logs el
        JOIN rooms r ON r.id = el.room_id
        WHERE r.building_id = %s {range_sql}
        """,
        (building_id, *range_params),
    )[0]

    return jsonify(
        building_id=building["id"],
        name=building["name"],
        total_kwh=_num(row["total_kwh"]),
        avg_kwh_per_log=_num(row["avg_kwh"]),
        avg_indoor_temp=_num(row["avg_temp"]),
        log_count=row["log_count"],
        cost_eur=_cost(row["total_kwh"]),
        carbon_kg_co2=_carbon(row["total_kwh"]),
        tariff_eur_per_kwh=TARIFF_EUR_PER_KWH,
        emission_kg_per_kwh=EMISSION_KG_PER_KWH,
    )


@app.route("/analytics/buildings/<int:building_id>/rooms", methods=["GET"])  # FR3.5
def analytics_by_room(building_id):
    _get_building(building_id)
    range_sql, range_params = _range_sql()
    rows = run_query(
        f"""
        SELECT r.id AS room_id, r.room_name,
               COALESCE(SUM(el.energy_consumed_kwh), 0) AS total_kwh
        FROM rooms r
        LEFT JOIN energy_logs el ON el.room_id = r.id {range_sql}
        WHERE r.building_id = %s
        GROUP BY r.id, r.room_name
        ORDER BY total_kwh DESC
        """,
        (*range_params, building_id),
    )
    return jsonify(
        [
            {
                "room_id": r["room_id"],
                "room_name": r["room_name"],
                "total_kwh": _num(r["total_kwh"]),
                "cost_eur": _cost(r["total_kwh"]),
                "carbon_kg_co2": _carbon(r["total_kwh"]),
            }
            for r in rows
        ]
    )


@app.route("/analytics/rooms/<int:room_id>/summary", methods=["GET"])  # FR3.5
def analytics_room_summary(room_id):
    room = _get_room(room_id)
    range_sql, range_params = _range_sql()
    row = run_query(
        f"""
        SELECT COALESCE(SUM(el.energy_consumed_kwh), 0) AS total_kwh,
               AVG(el.indoor_temp) AS avg_temp,
               COUNT(el.id) AS log_count
        FROM energy_logs el
        WHERE el.room_id = %s {range_sql}
        """,
        (room_id, *range_params),
    )[0]
    return jsonify(
        room_id=room["id"],
        room_name=room["room_name"],
        building_id=room["building_id"],
        total_kwh=_num(row["total_kwh"]),
        avg_indoor_temp=_num(row["avg_temp"]),
        log_count=row["log_count"],
        cost_eur=_cost(row["total_kwh"]),
        carbon_kg_co2=_carbon(row["total_kwh"]),
    )


@app.route("/analytics/buildings/<int:building_id>/trend", methods=["GET"])  # FR3.7, FR3.8
def analytics_trend(building_id):
    _get_building(building_id)
    period = request.args.get("period", "day")
    # %% is needed because the query also receives parameters.
    buckets = {
        "hour": "DATE_FORMAT(el.`timestamp`, '%%Y-%%m-%%d %%H:00')",
        "day": "DATE_FORMAT(el.`timestamp`, '%%Y-%%m-%%d')",
        "week": "DATE_FORMAT(el.`timestamp`, '%%x-W%%v')",
        "month": "DATE_FORMAT(el.`timestamp`, '%%Y-%%m')",
    }
    if period not in buckets:
        raise InvalidParameterError(f"'period' must be one of {sorted(buckets)}, got '{period}'")

    range_sql, range_params = _range_sql()
    rows = run_query(
        f"""
        SELECT {buckets[period]} AS bucket,
               SUM(el.energy_consumed_kwh) AS total_kwh,
               AVG(el.indoor_temp) AS avg_temp
        FROM energy_logs el
        JOIN rooms r ON r.id = el.room_id
        WHERE r.building_id = %s {range_sql}
        GROUP BY bucket
        ORDER BY bucket
        """,
        (building_id, *range_params),
    )
    return jsonify(
        period=period,
        points=[
            {
                "bucket": r["bucket"],
                "total_kwh": _num(r["total_kwh"]),
                "cost_eur": _cost(r["total_kwh"]),
                "carbon_kg_co2": _carbon(r["total_kwh"]),
                "avg_indoor_temp": _num(r["avg_temp"]),
            }
            for r in rows
        ],
    )


@app.route("/analytics/buildings/<int:building_id>/sustainability", methods=["GET"])  # FR3.4
def analytics_sustainability(building_id):
    building = _get_building(building_id)
    range_sql, range_params = _range_sql()
    row = run_query(
        f"""
        SELECT COALESCE(SUM(el.energy_consumed_kwh), 0) AS total_kwh,
               MIN(el.`timestamp`) AS first_log,
               MAX(el.`timestamp`) AS last_log
        FROM energy_logs el
        JOIN rooms r ON r.id = el.room_id
        WHERE r.building_id = %s {range_sql}
        """,
        (building_id, *range_params),
    )[0]

    if not row["first_log"]:
        return jsonify(building_id=building["id"], score=None, message="No energy data in this range")

    days = (row["last_log"] - row["first_log"]).days + 1
    score, intensity = _sustainability_score(row["total_kwh"], building["area_sqm"], days)
    if score is None:
        raise InvalidParameterError(f"Building {building_id} has no valid area_sqm")

    return jsonify(
        building_id=building["id"],
        name=building["name"],
        score=score,
        kwh_per_sqm=intensity,
        period_days=days,
        benchmark_kwh_per_sqm_year=BENCHMARK_KWH_PER_SQM_YEAR,
    )


@app.route("/analytics/buildings/<int:building_id>/anomalies", methods=["GET"])  # FR3.10
def analytics_anomalies(building_id):
    _get_building(building_id)
    try:
        threshold = float(request.args.get("threshold", 3.0))
    except ValueError:
        raise InvalidParameterError("'threshold' must be a number")
    if threshold <= 0:
        raise InvalidParameterError("'threshold' must be greater than 0")

    range_sql, range_params = _range_sql()
    rows = run_query(
        f"""
        SELECT el.id, el.room_id, el.`timestamp`, el.energy_consumed_kwh
        FROM energy_logs el
        JOIN rooms r ON r.id = el.room_id
        WHERE r.building_id = %s {range_sql}
        ORDER BY el.room_id, el.`timestamp`
        LIMIT 50000
        """,
        (building_id, *range_params),
    )

    by_room = {}
    for r in rows:
        by_room.setdefault(r["room_id"], []).append(r)

    found = []
    for room_id, logs in by_room.items():
        values = [float(l["energy_consumed_kwh"]) for l in logs]
        if len(values) < 3:
            continue
        mean, std = statistics.mean(values), statistics.pstdev(values)
        if std == 0:
            continue
        for log, value in zip(logs, values):
            z = (value - mean) / std
            if abs(z) > threshold:
                found.append(
                    {
                        "log_id": log["id"],
                        "room_id": room_id,
                        "timestamp": log["timestamp"].isoformat(),
                        "energy_consumed_kwh": _num(value),
                        "room_mean_kwh": _num(mean),
                        "z_score": _num(z),
                    }
                )

    found.sort(key=lambda a: abs(a["z_score"]), reverse=True)
    return jsonify(threshold=threshold, count=len(found), anomalies=found)


@app.route("/analytics/buildings/<int:building_id>/forecast", methods=["GET"])  # FR3.9
def analytics_forecast(building_id):
    _get_building(building_id)
    history_days = _int_arg("history_days", 30, 3, 365)
    horizon_days = _int_arg("horizon_days", 7, 1, 90)

    since = date.today() - timedelta(days=history_days)
    rows = run_query(
        """
        SELECT DATE(el.`timestamp`) AS day, SUM(el.energy_consumed_kwh) AS total_kwh
        FROM energy_logs el
        JOIN rooms r ON r.id = el.room_id
        WHERE r.building_id = %s AND el.`timestamp` >= %s
        GROUP BY DATE(el.`timestamp`)
        ORDER BY day
        """,
        (building_id, since),
    )
    if len(rows) < 3:
        raise InvalidParameterError("Not enough daily data to forecast (need at least 3 days)")

    first_day = rows[0]["day"]
    xs = [(r["day"] - first_day).days for r in rows]
    ys = [float(r["total_kwh"]) for r in rows]
    slope, intercept = statistics.linear_regression(xs, ys)

    last_x = xs[-1]
    predictions = []
    for step in range(1, horizon_days + 1):
        x = last_x + step
        kwh = max(0.0, slope * x + intercept)
        predictions.append(
            {
                "date": (first_day + timedelta(days=x)).isoformat(),
                "predicted_kwh": _num(kwh),
                "predicted_cost_eur": _cost(kwh),
            }
        )

    return jsonify(
        method="linear_regression_daily_totals",
        history_days_used=len(rows),
        trend_kwh_per_day=_num(slope),
        predictions=predictions,
    )


if __name__ == "__main__":
    app.run(debug=True)
