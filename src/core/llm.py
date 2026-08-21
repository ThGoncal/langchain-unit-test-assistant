"""
Configuration et initialisation du LLM principal de l'assistant.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

# print("LANGSMITH_TRACING:", os.getenv("LANGSMITH_TRACING"))
# print("LANGSMITH_PROJECT:", os.getenv("LANGSMITH_PROJECT"))

def get_llm(temperature: float = 0.0):
    """
    Retourne une instance configurée du LLM principal.

    temperature contrôle le degré d'aléatoire des réponses :
    - proche de 0 : sorties déterministes, recommandé pour les tâches
      d'analyse/génération structurée où la cohérence prime.
    - plus élevé (ex. 0.7) : sorties plus variées, adapté au chat libre.

    Le format "provider:model" (ex. "groq:openai/gpt-oss-120b") est géré
    nativement par init_chat_model, qui route vers le bon provider en fonction
    du préfixe. La clé API correspondante est lue automatiquement depuis
    l'environnement par le provider.
    """
    model_name = os.getenv("CHAT_MODEL", "groq:openai/gpt-oss-120b")
    return init_chat_model(model_name, temperature=temperature)