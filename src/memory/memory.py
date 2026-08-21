"""
Historique de conversation par utilisateur, tenu en mémoire process.

Distinct du checkpointer LangGraph utilisé par l'agent de chat (core/chains.py) :
celui-ci sert au modèle pour garder le fil de la conversation, celui-ci sert à
exposer l'historique côté API via /history, sous une forme simple.
"""

_histories: dict[str, list[dict[str, str]]] = {}


def add_message(username: str, role: str, content: str) -> None:
    """Ajoute un message à l'historique de l'utilisateur donné."""
    _histories.setdefault(username, []).append({"role": role, "content": content})


def get_history(username: str) -> list[dict[str, str]]:
    """Retourne l'historique complet de l'utilisateur donné (liste vide si aucun)."""
    return _histories.get(username, [])


def clear_history() -> None:
    """
    Réinitialise l'historique de tous les utilisateurs.

    Utilisé notamment dans les tests (setup_function) pour repartir d'un état
    propre entre chaque test. À ne pas exposer via un endpoint public en
    production.
    """
    _histories.clear()