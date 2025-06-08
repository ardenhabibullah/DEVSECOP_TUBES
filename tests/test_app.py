# tests/test_app.py

import pytest
from app import create_app, db
from app.models import Todo

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_empty_todo_list(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Belum ada tugas' in response.data

def test_add_todo(client):
    response = client.post('/add', data={'task': 'Test Task'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Task' in response.data

def test_toggle_todo(client):
    client.post('/add', data={'task': 'Toggle Task'})
    todo = Todo.query.first()
    response = client.get(f'/toggle/{todo.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'strike' in response.data or b'Toggle Task' in response.data

def test_delete_todo(client):
    client.post('/add', data={'task': 'Delete Task'})
    todo = Todo.query.first()
    response = client.get(f'/delete/{todo.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Delete Task' not in response.data
