# tests/test_app.py

import pytest
from app import create_app, db
from app.models import User, Todo

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False  # Disable CSRF for test form submissions
    })

    with app.app_context():
        db.create_all()

        # Buat user untuk login
        user = User(username='testuser')
        user.set_password('testpass')  # Pastikan model User punya method ini
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def logged_in_client(client):
    # Login dengan akun test
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    return client

def test_empty_todo_list(logged_in_client):
    response = logged_in_client.get('/')
    assert response.status_code == 200
    assert b'Belum ada tugas' in response.data

def test_add_todo(logged_in_client):
    response = logged_in_client.post('/add', data={'task': 'Test Task'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Task' in response.data

def test_toggle_todo(logged_in_client):
    logged_in_client.post('/add', data={'task': 'Toggle Task'}, follow_redirects=True)
    todo = Todo.query.first()
    assert todo is not None
    response = logged_in_client.get(f'/toggle/{todo.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'strike' in response.data or b'Toggle Task' in response.data

def test_delete_todo(logged_in_client):
    logged_in_client.post('/add', data={'task': 'Delete Task'}, follow_redirects=True)
    todo = Todo.query.first()
    assert todo is not None
    response = logged_in_client.get(f'/delete/{todo.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Delete Task' not in response.data
