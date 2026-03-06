from fastapi.testclient import TestClient
import pytest
from .api import app

client = TestClient(app)

# def test_read_main():
#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Hello World"}

@pytest.fixture
def data():
    return {
        'title': 'test title', 
        'equipment_type': 'test equipment type', 
        'chatbot_purpose': 'test chatbot purpose',
        'description': 'test description',
        'owner': 'test owner',
        'collection_name': 'test collection_name'
    }


def test_start_chat():
    response = client.get("/chats/3")
    assert response.status_code == 200
    assert response.json() == {"chat_id": 3, "collection_name": "test_collection"}
    assert response.cookies['collection_name'] == "test_collection"

def test_create_chatbot_config():
    # data = {
    #     'title': 'test title', 
    #     'equipment_type': 'test equipment type', 
    #     'chatbot_purpose': 'test chatbot purpose',
    #     'description': 'test description',
    #     'owner': 'test owner',
    #     'collection_name': 'test collection_name'
    # }
    with open('hpt.pdf', 'rb') as manual_file:
        files = {'file': manual_file}
        response = client.post("/manual_config_and_upload/", data=data, files=files)
    print(response.text)
    assert response.status_code == 200
    assert response.json() == {
        'name': 'test title', 
        'manual_title': 'test title', 
        'equipment_type': 'test equipment type', 
        'chatbot_purpose': 'test chatbot purpose',
        'description': 'test description',
        'owner': 'test owner',
        'collection_name': 'test collection_name',
        'file_name': 'hpt.pdf'
    }

class TestUserQuery:
    def test_user_query(self):
        pass