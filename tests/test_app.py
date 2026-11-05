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
