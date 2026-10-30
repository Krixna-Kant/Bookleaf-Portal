from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    bad = client.post("/api/v1/auth/login", json={"email": "priya.sharma@email.com", "password": "wrong"})
    expect(bad.status_code == 401, f"bad login status {bad.status_code}")
    expect(bad.json()["error"]["code"] == "INVALID_CREDENTIALS", bad.json())

    missing = client.get("/api/v1/auth/me")
    expect(missing.status_code == 401, f"missing token status {missing.status_code}")

    author = client.post(
        "/api/v1/auth/login",
        json={"email": "priya.sharma@email.com", "password": "Author@123"},
    )
    expect(author.status_code == 200, f"author login {author.status_code} {author.text}")
    author_body = author.json()
    expect(author_body["user"]["role"] == "author", author_body)
    expect(author_body["user"]["external_author_id"] == "AUTH001", author_body)
    expect(author_body["token_type"] == "bearer", author_body)

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {author_body['access_token']}"})
    expect(me.status_code == 200, f"author me {me.status_code} {me.text}")
    expect(me.json()["email"] == "priya.sharma@email.com", me.json())

    admin = client.post("/api/v1/auth/login", json={"email": "ops@bookleaf.com", "password": "Admin@123"})
    expect(admin.status_code == 200, f"admin login {admin.status_code} {admin.text}")
    expect(admin.json()["user"]["role"] == "admin", admin.json())

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": author_body["refresh_token"]})
    expect(refreshed.status_code == 200, f"refresh {refreshed.status_code} {refreshed.text}")

    using_refresh_as_access = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {author_body['refresh_token']}"},
    )
    expect(using_refresh_as_access.status_code == 401, using_refresh_as_access.text)

    print("AUTH TESTS PASSED")


if __name__ == "__main__":
    main()
