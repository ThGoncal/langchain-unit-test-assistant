"""
Vérifie que /analyze classe chaque échantillon de fixtures/code_samples/
dans la catégorie attendue (optimal/ vs non_optimal/), pour repérer une
dérive de comportement (prompt modifié, modèle changé, etc.).

Rappel important : le jugement du LLM n'est pas parfaitement déterministe
(voir README - Limites connues). Un désaccord isolé n'est pas forcément une
régression ; un désaccord systématique sur plusieurs exécutions l'est plus
probablement. Ce script est un canari, pas un test pass/fail strict.

Usage : PYTHONPATH=src uv run python scripts/regression_check.py
"""

from pathlib import Path

from fastapi.testclient import TestClient

from api.assistant import main
from api.authentification.auth import User

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "code_samples"

main.app.dependency_overrides[main.get_current_user] = lambda: User(username="regression_check")
client = TestClient(main.app)


def check_category(category: str, expected_is_optimal: bool) -> list[tuple[str, bool, bool]]:
    """Retourne une liste (nom_fichier, attendu, obtenu) pour une catégorie."""
    results = []
    folder = FIXTURES_DIR / category
    for file in sorted(folder.glob("*.py")):
        code = file.read_text(encoding="utf-8")
        response = client.post("/analyze", json={"code": code})
        actual = response.json()["is_optimal"] if response.status_code == 200 else None
        results.append((file.name, expected_is_optimal, actual))
    return results


def main_check():
    all_results = []
    all_results += check_category("optimal", expected_is_optimal=True)
    all_results += check_category("non_optimal", expected_is_optimal=False)

    mismatches = [r for r in all_results if r[1] != r[2]]

    print(f"{'Fichier':<30} {'Attendu':<10} {'Obtenu':<10} {'Statut'}")
    print("-" * 65)
    for name, expected, actual in all_results:
        status = "✅" if expected == actual else "❌ ÉCART"
        print(f"{name:<30} {str(expected):<10} {str(actual):<10} {status}")

    print(f"\n{len(all_results) - len(mismatches)}/{len(all_results)} conformes.")
    if mismatches:
        print(
            "\n⚠️  Écart(s) détecté(s) — rappel : is_optimal n'est pas parfaitement "
            "déterministe. Relance ce script 2-3 fois avant de conclure à une vraie "
            "régression plutôt qu'à un aléa ponctuel du modèle."
        )


if __name__ == "__main__":
    main_check()