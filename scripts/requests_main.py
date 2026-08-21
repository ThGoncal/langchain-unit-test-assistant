"""
Test manuel de l'API assistant, sans dépendre de l'API auth.
get_current_user est overridé pour simuler un utilisateur déjà authentifié.
Les chaînes LangChain, elles, restent réelles (vrai appel à Groq).
"""

from fastapi.testclient import TestClient

from api.assistant import main
from api.authentification.auth import User
from langchain_core.tracers.langchain import wait_for_all_tracers

main.app.dependency_overrides[main.get_current_user] = lambda: User(username="alice")
client = TestClient(main.app)

CODE_OPTIMAL = "def add(a: int, b: int) -> int:\n    \"\"\"Retourne la somme de a et b.\"\"\"\n    return a + b"
CODE_NON_OPTIMAL = "def add(a, b):\n    return a + b"

################################################################################################
print("--- /analyze (code optimal attendu) ---")
response = client.post("/analyze", json={"code": CODE_OPTIMAL})
print(response.status_code, response.json())

################################################################################################
print("\n--- /generate_test ---")
response = client.post("/generate_test", json={"code": CODE_OPTIMAL})
print(response.status_code, response.json())
generated_test = response.json()["unit_test"]

################################################################################################
print("\n--- /explain_test ---")
response = client.post(
    "/explain_test",
    json={"code": CODE_OPTIMAL, "unit_test": generated_test},
)
print(response.status_code, response.json())

################################################################################################
print("\n--- /full_pipeline (code optimal -> pipeline complet) ---")
response = client.post("/full_pipeline", json={"code": CODE_OPTIMAL})
print(response.status_code, response.json())

################################################################################################
print("\n--- /full_pipeline (code non optimal -> arrêt anticipé) ---")
response = client.post("/full_pipeline", json={"code": CODE_NON_OPTIMAL})
print(response.status_code, response.json())

################################################################################################
print("\n--- /chat ---")
response = client.post("/chat", json={"input": "Bonjour !"})
print(response.status_code, response.json())

################################################################################################
print("\n--- /history (doit contenir tous les échanges ci-dessus) ---")
response = client.get("/history")
print(response.status_code, response.json())
print(f"\nNombre total d'entrées dans l'historique : {len(response.json()['history'])}")

wait_for_all_tracers()  # bloque jusqu'à l'envoi complet des traces en attente