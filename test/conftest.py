import sys
import os
import pytest
from app import create_app, db

# Agrega el directorio raíz del proyecto a la ruta de búsqueda de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
