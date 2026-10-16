from tests.conftest import register_and_login

QUERY = {"query_text": "I paid Rs 5000 to an online seller and never received the goods"}


def test_register_rejects_duplicate_and_weak_password(client):
    ok = {"email": "a@example.com", "password": "correct-horse-battery"}
    assert client.post("/auth/register", json=ok).status_code == 201
    assert client.post("/auth/register", json=ok).status_code == 409
    assert client.post("/auth/register", json={"email": "b@example.com", "password": "short"}).status_code == 422


def test_login_wrong_password_is_401(client):
    register_and_login(client)
    r = client.post("/auth/login", data={"username": "a@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_cases_require_auth(client):
    assert client.get("/cases").status_code == 401
    assert client.post("/cases", json=QUERY).status_code == 401
    assert client.get("/cases", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_create_case_saves_everything_and_can_be_read_back(client):
    h = register_and_login(client)
    created = client.post("/cases", json=QUERY, headers=h)
    assert created.status_code == 201
    body = created.json()
    assert body["confidence"] == "high"
    assert body["facts"]["parties"] == ["buyer", "seller"]
    assert body["references"][0]["section"] == "318"
    assert body["response"]["guidance"]["applicable_provisions"][0]["source_id"].endswith("::318")

    listing = client.get("/cases", headers=h).json()
    assert [c["id"] for c in listing] == [body["id"]]
    assert "response" not in listing[0]  # list view is a summary

    detail = client.get(f"/cases/{body['id']}", headers=h)
    assert detail.status_code == 200 and detail.json()["query_text"] == QUERY["query_text"]


def test_users_cannot_see_each_others_cases(client):
    h1 = register_and_login(client, "a@example.com")
    h2 = register_and_login(client, "b@example.com")
    case_id = client.post("/cases", json=QUERY, headers=h1).json()["id"]
    assert client.get(f"/cases/{case_id}", headers=h2).status_code == 404
    assert client.get("/cases", headers=h2).json() == []


def test_me_and_docs(client):
    h = register_and_login(client)
    assert client.get("/users/me", headers=h).json()["email"] == "a@example.com"
    assert client.get("/docs").status_code == 200
