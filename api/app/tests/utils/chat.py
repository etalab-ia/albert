from fastapi.testclient import TestClient


def read_chats(client: TestClient, token):
    return client.get("/chats", headers={"Authorization": f"Bearer {token}"})


def create_chat(client: TestClient, token, chat_type):
    return client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "chat_type": chat_type,
        },
    )


def read_chat(client: TestClient, token, chat_id):
    return client.get(f"/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"})


def update_chat(client: TestClient, token, chat_id, **data):
    return client.post(f"/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"}, json=data)


def read_archive(client: TestClient, token, chat_id):
    return client.get(f"/chat/archive/{chat_id}", headers={"Authorization": f"Bearer {token}"})
