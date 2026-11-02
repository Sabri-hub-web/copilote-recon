"""Point d'entrée : python -m copilote "ta demande"

Exemples :
    python -m copilote "Analyse le scan donnees/scans_bench/scan_06.xml"
    python -m copilote "Scanne 127.0.0.1 et dis-moi par où commencer"
    python -m copilote "Scanne 8.8.8.8"            -> bloqué par le garde-fou
    python -m copilote --sans-memoire "..."         -> sans la brique 5
"""
import json
import sys
from datetime import datetime

from copilote import config
from copilote.agent import analyser
from copilote.llm import ClientLLM
from copilote.memoire import Memoire


def main():
    args = sys.argv[1:]
    sans_memoire = "--sans-memoire" in args
    args = [a for a in args if a != "--sans-memoire"]
    if not args:
        print(__doc__)
        return

    memoire = None if sans_memoire else Memoire(config.FICHIER_MEMOIRE)
    resultat = analyser(args[0], ClientLLM(), memoire=memoire)

    # On enregistre toute la trace (preuves pour EVIDENCE.md)
    config.DOSSIER_TRACES.mkdir(exist_ok=True)
    fichier = config.DOSSIER_TRACES / f"analyse_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    fichier.write_text(json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 70)
    # Les appels d'outil bloqués par un garde-fou (brique 3)
    for etape in resultat["trace"]:
        erreur = isinstance(etape.get("resultat"), dict) and etape["resultat"].get("erreur")
        if erreur:
            print(f"[GARDE-FOU] {etape['outil']}({etape['arguments']}) -> {erreur}")
    if resultat["statut"] == "validee":
        print("RÉPONSE VÉRIFIÉE\n")
        print(resultat["reponse"])
    else:
        print("RÉPONSE REJETÉE : le modèle n'a pas pu donner une réponse fidèle au scan.")
        for p in resultat["problemes"]:
            print("  -", p)
        if resultat["scan"]:
            print("\nPorts réellement ouverts (calculés par le code) :")
            for p in resultat["scan"]["ports_ouverts"]:
                print(f"  {p['port']}/{p['protocole']}  {p['service']}  {p['produit']}")
    print("=" * 70)
    print(f"Tokens : {resultat['tokens']}")
    print(f"Trace  : {fichier}")


if __name__ == "__main__":
    main()
