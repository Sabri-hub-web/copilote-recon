"""Affiche les échecs d'un benchmark avec leur trace, pour en expliquer un (brique 9).

    python bench/echecs.py resultats/bench_XXXX.json
"""
import json
import sys

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

donnees = json.load(open(sys.argv[1], encoding="utf-8"))
for lancement in donnees["lancements"]:
    for d in lancement["details"]:
        for qui in ("seul", "systeme"):
            if d[qui]["issue"] == "juste":
                continue
            print("=" * 70)
            print(f"Lancement {lancement['numero']} | {d['tache']} | {qui} | issue = {d[qui]['issue']}"
                  f" | inventés = {d[qui]['inventes']} | oubliés = {d[qui]['oublies']}")
            print(f"Vrais ports : {d['vrais_ports']}")
            for etape in d[qui]["trace"]:
                print("  -", json.dumps(etape, ensure_ascii=False)[:600])
