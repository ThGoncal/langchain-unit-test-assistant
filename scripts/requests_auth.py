"""
Script de test manuel de l'API d'authentification (hors pytest).
Nécessite que l'API tourne : uvicorn src.api.authentification.auth:app --port 8001
"""

import requests

BASE_URL = "http://localhost:8001"

#####################################################################
print("--- Signup : alice ---")
response = requests.post(
    f"{BASE_URL}/signup",
    json={"username": "alice", "password": "secret"},
)
print(f"Réponse : {response.json()}")
print(f"Statut  : {response.status_code}\n")

#####################################################################
print("--- Signup : alice (doublon attendu -> 400) ---")
response = requests.post(
    f"{BASE_URL}/signup",
    json={"username": "alice", "password": "secret"},
)
print(f"Réponse : {response.json()}")
print(f"Statut  : {response.status_code}\n")

#####################################################################
print("--- Login : mauvais mot de passe (attendu -> 401) ---")
response = requests.post(
    f"{BASE_URL}/login",
    json={"username": "alice", "password": "mauvais_mdp"},
)
print(f"Réponse : {response.json()}")
print(f"Statut  : {response.status_code}\n")

#####################################################################
print("--- Login : alice (attendu -> 200 + token) ---")
response = requests.post(
    f"{BASE_URL}/login",
    json={"username": "alice", "password": "secret"},
)
print(f"Réponse : {response.json()}")
print(f"Statut  : {response.status_code}\n")
token = response.json()["access_token"]

#####################################################################
print("--- /me sans token (attendu -> 401/403) ---")
response = requests.get(f"{BASE_URL}/me")
print(f"Statut  : {response.status_code}\n")

#####################################################################
print("--- /me avec token valide (attendu -> 200) ---")
response = requests.get(
    f"{BASE_URL}/me",
    headers={"Authorization": f"Bearer {token}"},
)
print(f"Réponse : {response.json()}")
print(f"Statut  : {response.status_code}\n")