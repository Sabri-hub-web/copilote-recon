"""BRIQUE 5 — La mémoire d'une session à l'autre.

Après chaque analyse VALIDÉE, on garde dans memoire.json :
la cible, la date, les ports ouverts et le début du résumé.
Quand on ré-analyse la même cible plus tard (même après avoir fermé le
programme), le modèle reçoit ce souvenir et peut dire ce qui a changé.

Coût : le souvenir est du texte en plus dans le contexte, donc des tokens en plus.
On l'estime avec estimer_tokens() et on le note dans la trace.
"""
import json
from datetime import datetime
from pathlib import Path


def estimer_tokens(texte: str) -> int:
    """Estimation grossière : environ 4 caractères par token."""
    return len(texte) // 4


class Memoire:
    def __init__(self, chemin):
        self.chemin = Path(chemin)
        self.donnees = {}
        if self.chemin.exists():                       # au démarrage : on relit le fichier
            self.donnees = json.loads(self.chemin.read_text(encoding="utf-8"))

    def rappeler(self, cible: str):
        """Renvoie le souvenir d'une cible, ou None si on ne la connaît pas."""
        return self.donnees.get(cible)

    def enregistrer(self, cible: str, ports: list, resume: str) -> None:
        """Ajoute/remplace le souvenir d'une cible et sauvegarde tout de suite."""
        self.donnees[cible] = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "ports_ouverts": sorted(ports),
            "resume": resume[:300],                    # on limite pour limiter les tokens
        }
        self.chemin.write_text(json.dumps(self.donnees, indent=2, ensure_ascii=False),
                               encoding="utf-8")

    def contexte_pour(self, cible: str) -> str:
        """Le texte du souvenir tel qu'on le donne au modèle (vide si aucun)."""
        souvenir = self.rappeler(cible)
        if souvenir is None:
            return ""
        return (f"Analyse précédente de {cible} le {souvenir['date']} : "
                f"ports ouverts {souvenir['ports_ouverts']}. "
                "Signale les ports apparus ou disparus depuis.")
