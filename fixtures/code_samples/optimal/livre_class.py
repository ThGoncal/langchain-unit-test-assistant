class Livre:
    """Représente un livre défini par son titre et son auteur."""

    def __init__(self, titre: str, auteur: str) -> None:
        if not titre or not titre.strip():
            raise ValueError("Le titre ne peut pas être vide.")
        if not auteur or not auteur.strip():
            raise ValueError("L'auteur ne peut pas être vide.")
        self.titre = titre
        self.auteur = auteur

    def __repr__(self) -> str:
        return f"Livre(titre={self.titre!r}, auteur={self.auteur!r})"

    def __str__(self) -> str:
        return f"{self.titre} de {self.auteur}"