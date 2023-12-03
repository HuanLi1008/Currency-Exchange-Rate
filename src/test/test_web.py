
import pytest
from src.main.app import create_app


@pytest.fixture
def app():
    app = create_app()
    
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200