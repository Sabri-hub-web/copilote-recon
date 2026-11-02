"""La connexion au modèle de langage (Qwen via Ollama, llama.cpp ou Cerebras).

Les trois parlent le format "OpenAI chat completions" : on envoie la liste
des messages (+ la liste des outils), on reçoit le message du modèle.
"""
import re

import requests

from copilote import config


def nettoyer(texte: str) -> str:
    """Enlève le raisonnement <think>...</think> que Qwen peut écrire avant sa réponse."""
    texte = texte or ""
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL)
    return texte.strip()


class ClientLLM:
    def __init__(self, base_url=None, modele=None, cle=None, temperature=None):
        self.base_url = (base_url or config.LLM_BASE_URL).rstrip("/")
        self.modele = modele or config.LLM_MODEL
        self.cle = cle if cle is not None else config.LLM_API_KEY
        self.temperature = config.LLM_TEMPERATURE if temperature is None else temperature

    def discuter(self, messages: list, outils=None):
        """Envoie la conversation au modèle. Renvoie (message, usage).

        message : dict avec "content" et éventuellement "tool_calls"
        usage   : dict avec "prompt_tokens" et "completion_tokens"
        """
        corps = {"model": self.modele, "messages": messages, "temperature": self.temperature}
        if outils:
            corps["tools"] = outils
        entetes = {"Authorization": f"Bearer {self.cle}"} if self.cle else {}
        try:
            r = requests.post(f"{self.base_url}/chat/completions", json=corps,
                              headers=entetes, timeout=config.LLM_TIMEOUT)
        except requests.ConnectionError:
            raise RuntimeError(f"Le modèle ne répond pas sur {self.base_url}. "
                               "Ollama est-il lancé ? (voir le README)") from None
        r.raise_for_status()
        donnees = r.json()
        return donnees["choices"][0]["message"], donnees.get("usage", {})
