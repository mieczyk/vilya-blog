import json

import pytest
from flask import session

from app import USER, app


@pytest.fixture
def client():
    app.config.update({"TESTING": True})
    yield app.test_client()


def test_login_sets_logged_in_flag_in_session_if_valid_credentials(client):
    with client:
        __sign_in(client)
        assert session["logged_in"]


def test_login_redirects_to_login_page_if_invalid_credentials(client):
    with client:
        response = client.post("/login", data={"login": "a", "password": "a"})
        assert "logged_in" not in session.keys()
        assert "<h1>Login</h1>" in response.get_data(as_text=True)


def test_logout_clears_session_data(client):
    with client:
        __sign_in(client)
        client.get("/logout")
        assert "logged_in" not in session.keys()


def test_sendout_forbidded_for_anonymous_users(client):
    expected_message = "Your nudes have been sent!"
    with client:
        # As anonymous user
        response = client.get("/sendout", follow_redirects=True)
        html_data = response.get_data(as_text=True)
        assert expected_message not in html_data
        assert "<h1>Login</h1>" in html_data

        # As signed-in user
        __sign_in(client)
        response = client.get("/sendout", follow_redirects=True)
        assert expected_message in response.get_data(as_text=True)


def test_change_password_forbidden_for_anonymous_users(client):
    expected_message = "Your password has been changed!"
    with client:
        # As anonymous user
        response = client.post(
            "/password",
            data=json.dumps({"new_password": "my_new_password"}),
            content_type="application/json",
            follow_redirects=True,
        )
        html_data = response.get_data(as_text=True)
        assert expected_message not in html_data
        assert "<h1>Login</h1>" in html_data

        # As signed-in user
        __sign_in(client)
        response = client.post(
            "/password",
            data=json.dumps({"new_password": "my_new_password"}),
            content_type="application/json",
            follow_redirects=True,
        )
        assert expected_message in response.get_data(as_text=True)


def __sign_in(client):
    return client.post(
        "/login", data={"login": USER["login"], "password": USER["password"]}
    )
