from collections.abc import Iterable


def moyenne(nombres: Iterable[float]) -> float:
    """Calcule la moyenne arithmétique des nombres fournis.

    Args:
        nombres: Itérable contenant les valeurs numériques.

    Returns:
        La moyenne des valeurs.

    Raises:
        ValueError: Si l'itérable est vide.
        TypeError: Si les valeurs ne peuvent pas être additionnées.
    """
    valeurs = list(nombres)

    if not valeurs:
        raise ValueError("Impossible de calculer la moyenne d'un ensemble vide.")

    return sum(valeurs) / len(valeurs)

def est_pair(nombre: int) -> bool:
    """Indique si un nombre entier est pair.

    Args:
        nombre: Nombre entier à tester.

    Returns:
        True si le nombre est pair, sinon False.
    """
    return nombre % 2 == 0