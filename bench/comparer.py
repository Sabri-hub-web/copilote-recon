"""BRIQUE 9 — Comparaison mesurée : "Qwen seul" contre "mon système".

  - 10 tâches dont on connaît la réponse (bench/taches.json)
  - chaque tâche est faite par les deux, 3 lancements chacun
  - on calcule moyenne et écart-type (dispersion) de chaque mesure
  - toutes les traces sont gardées pour expliquer un échec

    python bench/comparer.py                 (3 lancements, 10 tâches)
    python bench/comparer.py --lancements 1 --taches 3   (essai rapide)
"""
import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # pour "import copilote"

from copilote import config
from copilote.agent import analyser, modele_seul
from copilote.garde_fous import extraire_ligne_ports
from copilote.llm import ClientLLM

TACHES = Path(__file__).resolve().parent / "taches.json"


def noter(resultat: dict, vrais_ports: list) -> dict:
    """Note UNE réponse face à la bonne réponse.

    issue :
      "juste"   -> réponse montrée, et ses ports = exactement les vrais ports
      "fausse"  -> réponse montrée à l'utilisateur, mais ports faux  (le pire cas)
      "rejetee" -> le système a refusé de montrer une réponse
    """
    vrais = set(vrais_ports)
    if resultat["statut"] == "rejetee" or resultat.get("reponse") is None:
        return {"issue": "rejetee", "inventes": 0, "oublies": 0}
    annonces = extraire_ligne_ports(resultat["reponse"]) or set()
    inventes = len(annonces - vrais)
    oublies = len(vrais - annonces)
    issue = "juste" if (inventes == 0 and oublies == 0) else "fausse"
    return {"issue": issue, "inventes": inventes, "oublies": oublies}


def resumer(notes: list) -> dict:
    """Pour UN lancement (10 tâches) : taux de justes, de fausses, de rejets, ports inventés."""
    n = len(notes)
    return {
        "taux_juste": sum(x["issue"] == "juste" for x in notes) / n,
        "taux_fausse": sum(x["issue"] == "fausse" for x in notes) / n,
        "taux_rejetee": sum(x["issue"] == "rejetee" for x in notes) / n,
        "ports_inventes": sum(x["inventes"] for x in notes),
    }


def moyenne_ecart(valeurs: list) -> str:
    m = statistics.mean(valeurs)
    e = statistics.stdev(valeurs) if len(valeurs) > 1 else 0.0  # cas limite : 1 seul lancement
    return f"{m:.2f} ± {e:.2f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lancements", type=int, default=3)
    p.add_argument("--taches", type=int, default=10)
    args = p.parse_args()

    taches = json.loads(TACHES.read_text(encoding="utf-8"))[: args.taches]
    llm = ClientLLM()
    tout = {"modele": llm.modele, "date": datetime.now().isoformat(timespec="seconds"),
            "lancements": []}
    resumes = {"seul": [], "systeme": []}

    for n in range(args.lancements):
        notes = {"seul": [], "systeme": []}
        details = []
        for t in taches:
            print(f"lancement {n + 1}/{args.lancements}  {t['id']} ...", flush=True)
            r_seul = modele_seul(t["fichier"], llm)
            # memoire=None : chaque tâche est indépendante, pas de triche par la mémoire
            r_sys = analyser(f"Analyse le scan {t['fichier']}", llm, memoire=None)
            n_seul, n_sys = noter(r_seul, t["ports_ouverts"]), noter(r_sys, t["ports_ouverts"])
            notes["seul"].append(n_seul)
            notes["systeme"].append(n_sys)
            details.append({"tache": t["id"], "vrais_ports": t["ports_ouverts"],
                            "seul": {**n_seul, "trace": r_seul["trace"]},
                            "systeme": {**n_sys, "trace": r_sys["trace"]}})
        for qui in ("seul", "systeme"):
            resumes[qui].append(resumer(notes[qui]))
        tout["lancements"].append({"numero": n + 1, "details": details,
                                   "resume": {q: resumes[q][-1] for q in resumes}})

    # ---- Tableau final : moyenne ± écart-type sur les lancements ----
    lignes = ["| Mesure | Qwen seul | Mon système |", "|---|---|---|"]
    for cle, libelle in [("taux_juste", "Réponses justes (taux)"),
                         ("taux_fausse", "Réponses FAUSSES montrées (taux)"),
                         ("taux_rejetee", "Réponses rejetées (taux)"),
                         ("ports_inventes", "Ports inventés (total par lancement)")]:
        lignes.append(f"| {libelle} | {moyenne_ecart([r[cle] for r in resumes['seul']])} "
                      f"| {moyenne_ecart([r[cle] for r in resumes['systeme']])} |")
    tableau = "\n".join(lignes)
    tout["tableau"] = tableau

    dossier = config.RACINE / "resultats"
    dossier.mkdir(exist_ok=True)
    fichier = dossier / f"bench_{datetime.now():%Y%m%d_%H%M%S}.json"
    fichier.write_text(json.dumps(tout, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(taches)} tâches × {args.lancements} lancements — modèle {llm.modele}\n")
    print(tableau)
    print(f"\nDétails et traces : {fichier}")
    print("Pour voir les échecs : python bench/echecs.py " + str(fichier.relative_to(config.RACINE)))


if __name__ == "__main__":
    main()
