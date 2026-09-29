import os
import tempfile
from pathlib import Path
import pytest

ROOT = tempfile.TemporaryDirectory(prefix='rolefit-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(ROOT.name) / 'tests.db')
os.environ['APP_PASSWORD'] = 'test-workspace-password'
os.environ['SESSION_SECRET'] = 'a-test-session-secret-of-at-least-32-characters'
os.environ['APP_ENV'] = 'test'
os.environ['COOKIE_SECURE'] = 'false'
os.environ['GROQ_API_KEY'] = ''
os.environ['OPENROUTER_API_KEY'] = ''
os.environ['OLLAMA_BASE_URL'] = ''
os.environ.pop('RENDER', None)

from app.db import Base, engine, put_state
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

@pytest.fixture
def headers(client):
    client.cookies.clear()
    response = client.post('/api/login', json={'password': os.environ['APP_PASSWORD']}, headers={'X-RoleFit-Request': '1'})
    assert response.status_code == 200, response.text
    return {'X-RoleFit-Request': '1', 'X-CSRF-Token': response.json()['csrf']}

@pytest.fixture
def document():
    from app.parsing import parse_text
    doc, _ = parse_text('Alex Example\nJava Developer\nEmail: alex@example.com\nPROFESSIONAL SUMMARY\n- Built Java APIs with Spring Boot.\nTECHNICAL SKILLS\nJava, React, PostgreSQL, Docker\nPROFESSIONAL EXPERIENCE\nCLIENT: Example Company\n- Developed REST APIs and automated tests.\n- Built React dashboards for service monitoring.\n- Created Docker deployment workflows.\nEDUCATION\nBS Computer Science, Example University')
    return doc.model_dump()

@pytest.fixture
def profile(document):
    put_state('profile', {'document': document, 'confirmed': True})
    return document
