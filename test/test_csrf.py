import pytest
from flask import url_for
from app import create_app, db

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///:memory:',
        "WTF_CSRF_ENABLED": True,
        "SERVER_NAME": "localhost.localdomain",
        "APPLICATION_ROOT": "/",
        "PREFERRED_URL_SCHEME": "http"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_csrf_token(client):
    with client:
        response = client.get(url_for('main.home'))
        assert response.status_code == 200
        assert 'csrf_token' in response.get_data(as_text=True)

def test_protected_post_request(client):
    with client:
        response = client.post(url_for('main.translate_post', post_id=1), json={
            'language': 'es',
            'content': 'Testing content'
        })
        assert response.status_code == 400  # CSRF token missing or incorrect

def test_post_request_with_csrf(client):
    with client:
        # First get the CSRF token
        response = client.get(url_for('main.home'))
        assert response.status_code == 200
        csrf_token = response.headers.get('Set-Cookie').split('csrf_token=')[1].split(';')[0]

        # Now use this token in a POST request
        response = client.post(url_for('main.translate_post', post_id=1), json={
            'language': 'es',
            'content': 'Testing content'
        }, headers={
            'X-CSRFToken': csrf_token
        })
        assert response.status_code != 400
