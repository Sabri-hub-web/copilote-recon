"""Outils partagés par les tests.

FauxLLM remplace Qwen : il renvoie des réponses écrites à l'avance.
Comme ça, les tests ont une réponse CONNUE, tournent en 1 seconde,
et passent même sur une machine sans modèle (exigence R2).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FauxLLM:
    def __init__(self, reponses):
        self.reponses = list(reponses)   # file d'attente des réponses à donner
        self.recus = []                  # ce que l'agent a envoyé (pour vérifier)

    def discuter(self, messages, outils=None):
        self.recus.append([dict(m) for m in messages])
        message = self.reponses.pop(0)
        return message, {"prompt_tokens": 100, "completion_tokens": 20}


def appel_outil(nom, **arguments):
    """Fabrique un message du modèle qui demande un outil."""
    return {"content": "", "tool_calls": [{
        "id": f"appel_{nom}", "type": "function",
        "function": {"name": nom, "arguments": json.dumps(arguments)}}]}


def texte(contenu):
    """Fabrique un message texte du modèle."""
    return {"content": contenu}


@pytest.fixture
def scan_01():
    return "donnees/scans_bench/scan_01.xml"   # vrais ports ouverts : 22 et 80
