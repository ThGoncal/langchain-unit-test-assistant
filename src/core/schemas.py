from pydantic import BaseModel, Field


# --- Schémas de sortie structurée du LLM (utilisés via with_structured_output) ---

class CodeAnalysisResult(BaseModel):
    is_optimal: bool = Field(
        description="True si le code est jugé optimal et correct, False sinon"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Problèmes identifiés dans le code (style, bugs, mauvaises pratiques). Liste vide si le code est optimal."
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggestions concrètes pour corriger ou améliorer le code. Liste vide si le code est optimal."
    )


class GeneratedTestResult(BaseModel):
    unit_test: str = Field(
        description="Code Python complet d'un test unitaire pytest pour la fonction fournie, prêt à être exécuté"
    )


class ExplainTestRequest(BaseModel):
    code: str = Field(description="Code Python source concerné")
    unit_test: str = Field(description="Test unitaire à expliquer")


class TestExplanationResult(BaseModel):
    explanation: str = Field(
        description="Explication claire et pédagogique de ce que teste le test unitaire et pourquoi"
    )

# --- Schémas d'entrée/sortie des endpoints FastAPI ---

class CodeRequest(BaseModel):
    code: str = Field(description="Code Python source à analyser")


class ChatRequest(BaseModel):
    input: str = Field(description="Message envoyé par l'utilisateur à l'assistant")


class ChatResponse(BaseModel):
    response: str = Field(description="Réponse générée par l'assistant")


class HistoryItem(BaseModel):
    role: str = Field(description="'user' ou 'assistant'")
    content: str = Field(description="Contenu du message")


class HistoryResponse(BaseModel):
    history: list[HistoryItem] = Field(
        default_factory=list,
        description="Historique complet des échanges pour l'utilisateur courant"
    )
