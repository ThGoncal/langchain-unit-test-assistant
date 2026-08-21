"""
Test d'intégration manuel : les deux APIs tournent en parallèle, sans mock.
Prérequis :
  Terminal 1 : uv run uvicorn api.authentification.auth:app --app-dir src --reload --port 8001
  Terminal 2 : AUTH_URL=http://localhost:8001 uv run uvicorn api.assistant.main:app --app-dir src --reload --port 8000
"""

import requests

AUTH_URL = "http://localhost:8001"
MAIN_URL = "http://localhost:8000"


def signup_and_login(username: str, password: str = "secret") -> str:
    requests.post(f"{AUTH_URL}/signup", json={"username": username, "password": password})
    response = requests.post(f"{AUTH_URL}/login", json={"username": username, "password": password})
    response.raise_for_status()
    return response.json()["access_token"]

################################################################################################################
print("--- 1. Signup + login sur l'API auth ---")
token = signup_and_login("integration_user")
print(f"Token obtenu : {token[:20]}...\n")

################################################################################################################
print("--- 2. /chat SANS token (attendu -> 401, via délégation à /me) ---")
response = requests.post(f"{MAIN_URL}/chat", json={"input": "Bonjour !"})
print(response.status_code, response.json(), "\n")

################################################################################################################
print("--- 3. /chat avec un token invalide (attendu -> 401) ---")
response = requests.post(
    f"{MAIN_URL}/chat",
    json={"input": "Bonjour !"},
    headers={"Authorization": "Bearer token-invalide"},
)
print(response.status_code, response.json(), "\n")

################################################################################################################
print("--- 4. /chat avec un VRAI token (attendu -> 200, délégation réussie) ---")
response = requests.post(
    f"{MAIN_URL}/chat",
    json={"input": "Bonjour, je m'appelle integration_user."},
    headers={"Authorization": f"Bearer {token}"},
)
print(response.status_code, response.json(), "\n")

################################################################################################################
print("--- 5. /history avec le même token (doit refléter l'échange ci-dessus) ---")
response = requests.get(f"{MAIN_URL}/history", headers={"Authorization": f"Bearer {token}"})
print(response.status_code, response.json(), "\n")

################################################################################################################
print("--- 6. /analyze avec le token (vérifie que la délégation marche sur un autre endpoint aussi) ---")
response = requests.post(
    f"{MAIN_URL}/analyze",
    json={"code": "def add(a, b):\n    return a + b"},
    headers={"Authorization": f"Bearer {token}"},
)
print(response.status_code, response.json())