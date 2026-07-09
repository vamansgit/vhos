def test_signup_creates_brand_and_owner(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "brand_name": "New Brand",
            "category": "beauty",
            "full_name": "Founder",
            "email": "founder@brand.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_signup_duplicate_email_rejected(client):
    payload = {
        "brand_name": "Brand A",
        "full_name": "Owner",
        "email": "dup@brand.com",
        "password": "password123",
    }
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 409


def test_login_with_correct_credentials(client):
    client.post(
        "/api/auth/signup",
        json={
            "brand_name": "Brand B",
            "full_name": "Owner B",
            "email": "loginuser@brand.com",
            "password": "correcthorse",
        },
    )
    response = client.post(
        "/api/auth/login-json", json={"email": "loginuser@brand.com", "password": "correcthorse"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_rejected(client):
    client.post(
        "/api/auth/signup",
        json={
            "brand_name": "Brand C",
            "full_name": "Owner C",
            "email": "wrongpass@brand.com",
            "password": "correcthorse",
        },
    )
    response = client.post(
        "/api/auth/login-json", json={"email": "wrongpass@brand.com", "password": "nope"}
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "owner@test.com"
