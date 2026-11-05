from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pymysql
import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


# --- home ---------------------------------------------------------------

def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_home_returns_welcome_message(client):
    response = client.get("/")
    assert "message" in response.get_json()


# --- users ----------------------------------------------------------------

def test_list_users_success(client):
    fake_users = [{"id": 1, "username": "alice", "role": "admin"}]
    with patch("app.run_query", return_value=fake_users):
        response = client.get("/users")
    assert response.status_code == 200
    assert response.get_json() == fake_users


def test_list_users_empty(client):
    with patch("app.run_query", return_value=[]):
        response = client.get("/users")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_users_db_connection_error_returns_503(client):
    with patch("app.get_connection", side_effect=pymysql.MySQLError("connection refused")):
        response = client.get("/users")
    assert response.status_code == 503
    assert "error" in response.get_json()


# --- buildings --------------------------------------------------------------

def test_list_buildings_success(client):
    fake_buildings = [{"id": 1, "user_id": 1, "name": "HQ", "area_sqm": 500.0}]
    with patch("app.run_query", return_value=fake_buildings):
        response = client.get("/buildings")
    assert response.status_code == 200
    assert response.get_json() == fake_buildings


def test_list_buildings_query_error_returns_503(client):
    bad_cursor = MagicMock()
    bad_cursor.__enter__.return_value.execute.side_effect = pymysql.MySQLError("bad query")
    bad_cursor.__exit__.return_value = False
    bad_connection = MagicMock()
    bad_connection.cursor.return_value = bad_cursor

    with patch("app.get_connection", return_value=bad_connection):
        response = client.get("/buildings")

    assert response.status_code == 503
    bad_connection.close.assert_called_once()


# --- rooms --------------------------------------------------------------

def test_list_rooms_success(client):
    fake_rooms = [{"id": 1, "building_id": 1, "occupant_id": None, "room_name": "A1"}]
    with patch("app.run_query", side_effect=[[{"id": 1}], fake_rooms]):
        response = client.get("/buildings/1/rooms")
    assert response.status_code == 200
    assert response.get_json() == fake_rooms


def test_list_rooms_invalid_building_id_returns_400(client):
    response = client.get("/buildings/0/rooms")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_list_rooms_building_not_found_returns_404(client):
    with patch("app.run_query", return_value=[]):
        response = client.get("/buildings/999/rooms")
    assert response.status_code == 404
    assert "error" in response.get_json()


# --- generic error handling ----------------------------------------------

def test_unknown_route_returns_404(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_error_response_has_json_error_key(client):
    with patch("app.run_query", return_value=[]):
        response = client.get("/buildings/1/rooms")
    body = response.get_json()
    assert response.status_code == 404
    assert isinstance(body, dict)
    assert "error" in body


# ===========================================================================
# Subsystem 3: analytics APIs
# ===========================================================================

BUILDING = {"id": 1, "name": "HQ", "area_sqm": 500.0}
ROOM = {"id": 1, "building_id": 1, "room_name": "A1"}


@pytest.fixture(autouse=True)
def fixed_rates(monkeypatch):
    """Keep the tests independent of any env vars on your machine."""
    monkeypatch.setattr(app_module, "TARIFF_EUR_PER_KWH", 0.30)
    monkeypatch.setattr(app_module, "EMISSION_KG_PER_KWH", 0.40)
    monkeypatch.setattr(app_module, "BENCHMARK_KWH_PER_SQM_YEAR", 100.0)


def make_logs(values, room_id=1):
    start = datetime(2026, 1, 1)
    return [
        {
            "id": i + 1,
            "room_id": room_id,
            "timestamp": start + timedelta(hours=i),
            "energy_consumed_kwh": v,
        }
        for i, v in enumerate(values)
    ]


# --- dashboard (FR3.1, FR3.6) -----------------------------------------------

def test_analytics_dashboard_success(client):
    rows = [
        {"id": 1, "name": "HQ", "area_sqm": 500.0, "total_kwh": 100.0,
         "first_log": datetime(2026, 1, 1), "last_log": datetime(2026, 1, 10)},
        {"id": 2, "name": "Annex", "area_sqm": 100.0, "total_kwh": 50.0,
         "first_log": datetime(2026, 1, 1), "last_log": datetime(2026, 1, 10)},
    ]
    with patch("app.run_query", return_value=rows):
        response = client.get("/analytics/dashboard")
    body = response.get_json()
    assert response.status_code == 200
    assert body["totals"] == {"total_kwh": 150.0, "cost_eur": 45.0, "carbon_kg_co2": 60.0}
    assert len(body["buildings"]) == 2
    assert body["buildings"][0]["cost_eur"] == 30.0


def test_analytics_dashboard_no_buildings(client):
    with patch("app.run_query", return_value=[]):
        response = client.get("/analytics/dashboard")
    body = response.get_json()
    assert response.status_code == 200
    assert body["totals"]["total_kwh"] == 0
    assert body["buildings"] == []


def test_analytics_dashboard_building_without_logs(client):
    rows = [{"id": 1, "name": "HQ", "area_sqm": 500.0, "total_kwh": 0,
             "first_log": None, "last_log": None}]
    with patch("app.run_query", return_value=rows):
        response = client.get("/analytics/dashboard")
    assert response.status_code == 200
    assert response.get_json()["totals"]["total_kwh"] == 0


# --- building summary (FR3.2, FR3.3) ----------------------------------------

def test_analytics_building_summary_success(client):
    row = {"total_kwh": 100.0, "avg_kwh": 2.5, "avg_temp": 21.5, "log_count": 40}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/summary")
    body = response.get_json()
    assert response.status_code == 200
    assert body["total_kwh"] == 100.0
    assert body["cost_eur"] == 30.0          # 100 kWh * 0.30
    assert body["carbon_kg_co2"] == 40.0     # 100 kWh * 0.40
    assert body["log_count"] == 40


def test_analytics_building_summary_uses_configured_tariff(client, monkeypatch):
    monkeypatch.setattr(app_module, "TARIFF_EUR_PER_KWH", 0.50)
    row = {"total_kwh": 100.0, "avg_kwh": 2.5, "avg_temp": 21.5, "log_count": 40}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/summary")
    assert response.get_json()["cost_eur"] == 50.0


def test_analytics_building_summary_rounds_to_two_decimals(client):
    row = {"total_kwh": 10.12345, "avg_kwh": 1.11111, "avg_temp": 20.98765, "log_count": 9}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/summary")
    body = response.get_json()
    assert body["total_kwh"] == 10.12
    assert body["avg_kwh_per_log"] == 1.11
    assert body["avg_indoor_temp"] == 20.99


def test_analytics_building_summary_with_no_logs_returns_zeros(client):
    row = {"total_kwh": 0, "avg_kwh": None, "avg_temp": None, "log_count": 0}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/summary")
    body = response.get_json()
    assert response.status_code == 200
    assert body["total_kwh"] == 0
    assert body["cost_eur"] == 0


def test_analytics_building_summary_accepts_date_range(client):
    row = {"total_kwh": 10.0, "avg_kwh": 1.0, "avg_temp": 20.0, "log_count": 10}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]) as mock_query:
        response = client.get("/analytics/buildings/1/summary?start=2026-01-01&end=2026-01-31")
    assert response.status_code == 200
    # the second query must receive the building id plus both dates
    params = mock_query.call_args_list[1][0][1]
    assert params[0] == 1
    assert params[1] == date(2026, 1, 1)
    assert params[2] == date(2026, 2, 1)     # end is inclusive, so the next day


# --- consumption by room (FR3.5) --------------------------------------------

def test_analytics_by_room_success(client):
    rows = [
        {"room_id": 2, "room_name": "B1", "total_kwh": 80.0},
        {"room_id": 1, "room_name": "A1", "total_kwh": 20.0},
    ]
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/rooms")
    body = response.get_json()
    assert response.status_code == 200
    assert [r["room_id"] for r in body] == [2, 1]
    assert body[0]["cost_eur"] == 24.0
    assert body[0]["carbon_kg_co2"] == 32.0


def test_analytics_by_room_empty(client):
    with patch("app.run_query", side_effect=[[BUILDING], []]):
        response = client.get("/analytics/buildings/1/rooms")
    assert response.status_code == 200
    assert response.get_json() == []


# --- room summary (FR3.5) ---------------------------------------------------

def test_analytics_room_summary_success(client):
    row = {"total_kwh": 50.0, "avg_temp": 22.0, "log_count": 25}
    with patch("app.run_query", side_effect=[[ROOM], [row]]):
        response = client.get("/analytics/rooms/1/summary")
    body = response.get_json()
    assert response.status_code == 200
    assert body["room_name"] == "A1"
    assert body["building_id"] == 1
    assert body["cost_eur"] == 15.0
    assert body["carbon_kg_co2"] == 20.0


def test_analytics_room_summary_invalid_id_returns_400(client):
    response = client.get("/analytics/rooms/0/summary")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_analytics_room_summary_not_found_returns_404(client):
    with patch("app.run_query", return_value=[]):
        response = client.get("/analytics/rooms/999/summary")
    assert response.status_code == 404
    assert "error" in response.get_json()


# --- trend (FR3.7, FR3.8) ---------------------------------------------------

def test_analytics_trend_default_period_is_day(client):
    rows = [
        {"bucket": "2026-01-01", "total_kwh": 10.0, "avg_temp": 21.0},
        {"bucket": "2026-01-02", "total_kwh": 20.0, "avg_temp": 22.0},
    ]
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/trend")
    body = response.get_json()
    assert response.status_code == 200
    assert body["period"] == "day"
    assert len(body["points"]) == 2
    assert body["points"][0]["cost_eur"] == 3.0
    assert body["points"][0]["carbon_kg_co2"] == 4.0
    assert body["points"][1]["avg_indoor_temp"] == 22.0


@pytest.mark.parametrize("period", ["hour", "day", "week", "month"])
def test_analytics_trend_accepts_all_periods(client, period):
    with patch("app.run_query", side_effect=[[BUILDING], []]):
        response = client.get(f"/analytics/buildings/1/trend?period={period}")
    assert response.status_code == 200
    assert response.get_json()["period"] == period


def test_analytics_trend_invalid_period_returns_400(client):
    with patch("app.run_query", return_value=[BUILDING]):
        response = client.get("/analytics/buildings/1/trend?period=year")
    assert response.status_code == 400
    assert "error" in response.get_json()


# --- sustainability score (FR3.4) -------------------------------------------

def test_analytics_sustainability_success(client):
    # 5000 kWh / 500 m2 = 10 kWh/m2 over 10 days
    # benchmark = 100 * 10 / 365 = 2.74, so score = 100 * 2.74 / 10 = 27.4
    row = {"total_kwh": 5000.0,
           "first_log": datetime(2026, 1, 1), "last_log": datetime(2026, 1, 10)}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/sustainability")
    body = response.get_json()
    assert response.status_code == 200
    assert body["kwh_per_sqm"] == 10.0
    assert body["period_days"] == 10
    assert body["score"] == pytest.approx(27.4, abs=0.01)


def test_analytics_sustainability_score_is_capped_at_100(client):
    row = {"total_kwh": 10.0,
           "first_log": datetime(2026, 1, 1), "last_log": datetime(2026, 12, 31)}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/sustainability")
    assert response.get_json()["score"] == 100.0


def test_analytics_sustainability_no_data_returns_null_score(client):
    row = {"total_kwh": 0, "first_log": None, "last_log": None}
    with patch("app.run_query", side_effect=[[BUILDING], [row]]):
        response = client.get("/analytics/buildings/1/sustainability")
    body = response.get_json()
    assert response.status_code == 200
    assert body["score"] is None
    assert "message" in body


def test_analytics_sustainability_zero_area_returns_400(client):
    building = {"id": 1, "name": "HQ", "area_sqm": 0}
    row = {"total_kwh": 100.0,
           "first_log": datetime(2026, 1, 1), "last_log": datetime(2026, 1, 5)}
    with patch("app.run_query", side_effect=[[building], [row]]):
        response = client.get("/analytics/buildings/1/sustainability")
    assert response.status_code == 400
    assert "error" in response.get_json()


# --- anomalies (FR3.10) -----------------------------------------------------

def test_analytics_anomalies_detects_spike(client):
    logs = make_logs([2.0] * 19 + [40.0])
    with patch("app.run_query", side_effect=[[BUILDING], logs]):
        response = client.get("/analytics/buildings/1/anomalies?threshold=3")
    body = response.get_json()
    assert response.status_code == 200
    assert body["count"] == 1
    assert body["anomalies"][0]["log_id"] == 20
    assert body["anomalies"][0]["energy_consumed_kwh"] == 40.0
    assert body["anomalies"][0]["z_score"] == pytest.approx(4.36, abs=0.01)


def test_analytics_anomalies_flat_data_returns_none(client):
    logs = make_logs([2.0] * 10)
    with patch("app.run_query", side_effect=[[BUILDING], logs]):
        response = client.get("/analytics/buildings/1/anomalies")
    body = response.get_json()
    assert response.status_code == 200
    assert body["count"] == 0
    assert body["anomalies"] == []


def test_analytics_anomalies_skips_rooms_with_too_few_logs(client):
    logs = make_logs([2.0, 50.0])
    with patch("app.run_query", side_effect=[[BUILDING], logs]):
        response = client.get("/analytics/buildings/1/anomalies?threshold=1")
    assert response.get_json()["count"] == 0


def test_analytics_anomalies_lower_threshold_finds_more(client):
    values = [2.0] * 17 + [3.5, 40.0, 3.0]
    with patch("app.run_query", side_effect=[[BUILDING], make_logs(values)]):
        strict = client.get("/analytics/buildings/1/anomalies?threshold=3").get_json()
    with patch("app.run_query", side_effect=[[BUILDING], make_logs(values)]):
        loose = client.get("/analytics/buildings/1/anomalies?threshold=0.5").get_json()
    assert loose["count"] > strict["count"]


def test_analytics_anomalies_sorted_by_strength(client):
    values = [2.0] * 16 + [20.0, 40.0, 30.0, 2.0]
    with patch("app.run_query", side_effect=[[BUILDING], make_logs(values)]):
        body = client.get("/analytics/buildings/1/anomalies?threshold=1").get_json()
    z_scores = [abs(a["z_score"]) for a in body["anomalies"]]
    assert z_scores == sorted(z_scores, reverse=True)


# --- forecast (FR3.9) -------------------------------------------------------

def daily_rows(values):
    return [
        {"day": date(2026, 1, 1) + timedelta(days=i), "total_kwh": v}
        for i, v in enumerate(values)
    ]


def test_analytics_forecast_follows_linear_trend(client):
    rows = daily_rows([10.0, 20.0, 30.0, 40.0, 50.0])
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/forecast?horizon_days=3")
    body = response.get_json()
    assert response.status_code == 200
    assert body["trend_kwh_per_day"] == 10.0
    assert [p["predicted_kwh"] for p in body["predictions"]] == [60.0, 70.0, 80.0]
    assert body["predictions"][0]["date"] == "2026-01-06"
    assert body["predictions"][0]["predicted_cost_eur"] == 18.0


def test_analytics_forecast_never_predicts_negative_kwh(client):
    rows = daily_rows([30.0, 20.0, 10.0])
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/forecast?horizon_days=3")
    predictions = response.get_json()["predictions"]
    assert all(p["predicted_kwh"] >= 0 for p in predictions)


def test_analytics_forecast_default_horizon_is_7_days(client):
    rows = daily_rows([10.0, 20.0, 30.0])
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/forecast")
    assert len(response.get_json()["predictions"]) == 7


def test_analytics_forecast_needs_at_least_three_days(client):
    rows = daily_rows([10.0, 20.0])
    with patch("app.run_query", side_effect=[[BUILDING], rows]):
        response = client.get("/analytics/buildings/1/forecast")
    assert response.status_code == 400
    assert "error" in response.get_json()


# --- shared validation and error handling -----------------------------------

@pytest.mark.parametrize(
    "url",
    [
        "/analytics/dashboard?start=not-a-date",
        "/analytics/buildings/1/summary?start=2026-13-01",
        "/analytics/buildings/1/summary?end=01-02-2026",
        "/analytics/buildings/1/summary?start=2026-12-01&end=2026-01-01",
        "/analytics/buildings/1/rooms?start=bad",
        "/analytics/rooms/1/summary?start=bad",
        "/analytics/buildings/1/trend?period=year",
        "/analytics/buildings/1/anomalies?threshold=abc",
        "/analytics/buildings/1/anomalies?threshold=0",
        "/analytics/buildings/1/anomalies?threshold=-2",
        "/analytics/buildings/1/forecast?horizon_days=500",
        "/analytics/buildings/1/forecast?horizon_days=0",
        "/analytics/buildings/1/forecast?history_days=abc",
        "/analytics/buildings/0/summary",
        "/analytics/buildings/0/rooms",
        "/analytics/buildings/0/trend",
        "/analytics/buildings/0/sustainability",
        "/analytics/buildings/0/anomalies",
        "/analytics/buildings/0/forecast",
    ],
)
def test_analytics_bad_input_returns_400(client, url):
    with patch("app.run_query", return_value=[BUILDING]):
        response = client.get(url)
    assert response.status_code == 400
    assert "error" in response.get_json()


@pytest.mark.parametrize(
    "url",
    [
        "/analytics/buildings/999/summary",
        "/analytics/buildings/999/rooms",
        "/analytics/buildings/999/trend",
        "/analytics/buildings/999/sustainability",
        "/analytics/buildings/999/anomalies",
        "/analytics/buildings/999/forecast",
    ],
)
def test_analytics_unknown_building_returns_404(client, url):
    with patch("app.run_query", return_value=[]):
        response = client.get(url)
    assert response.status_code == 404
    assert "error" in response.get_json()


@pytest.mark.parametrize(
    "url",
    [
        "/analytics/dashboard",
        "/analytics/buildings/1/summary",
        "/analytics/buildings/1/forecast",
        "/analytics/rooms/1/summary",
    ],
)
def test_analytics_db_connection_error_returns_503(client, url):
    with patch("app.get_connection", side_effect=pymysql.MySQLError("connection refused")):
        response = client.get(url)
    assert response.status_code == 503
    assert "error" in response.get_json()
