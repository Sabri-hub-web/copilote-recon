"""BRIQUE 1 — Mes propres outils, que le modèle appelle.

  - lire_scan(chemin)  : lit un fichier XML produit par nmap et renvoie
                         la cible + la liste des ports OUVERTS.
  - lancer_scan(cible) : lance nmap sur une cible AUTORISÉE puis lit le résultat.

Le modèle ne lit jamais le XML lui-même : il reçoit ce que ces fonctions
ont calculé. C'est la "source de vérité" du système.
"""
import subprocess
import time
import xml.etree.ElementTree as ET

from copilote import config
from copilote.garde_fous import verifier_chemin, verifier_cible


def lire_scan(chemin: str) -> dict:
    """Lit un scan nmap (format XML, option -oX) et garde seulement les ports ouverts.

    Exemple de résultat :
      {"cible": "172.17.0.2",
       "ports_ouverts": [{"port": 22, "protocole": "tcp", "service": "ssh",
                          "produit": "OpenSSH 8.9p1"}]}
    """
    fichier = verifier_chemin(chemin)       # règle de la brique 3 : dossier donnees/ seulement
    racine = ET.parse(fichier).getroot()    # <nmaprun> ... </nmaprun>

    hote = racine.find("host")
    if hote is None:                        # cas limite : nmap n'a trouvé aucun hôte
        return {"cible": None, "ports_ouverts": []}

    adresse = hote.find("address")
    cible = adresse.get("addr") if adresse is not None else None

    ports = []
    for port in hote.iter("port"):          # chaque <port protocol="tcp" portid="22">
        etat = port.find("state")
        # "closed", "filtered", "open|filtered" ne comptent PAS : seulement "open"
        if etat is None or etat.get("state") != "open":
            continue
        service = port.find("service")
        if service is not None:
            nom = service.get("name", "inconnu")
            produit = " ".join(x for x in [service.get("product"), service.get("version")] if x)
        else:
            nom, produit = "inconnu", ""
        ports.append({
            "port": int(port.get("portid")),
            "protocole": port.get("protocol"),
            "service": nom,
            "produit": produit,
        })

    ports.sort(key=lambda p: p["port"])
    return {"cible": cible, "ports_ouverts": ports}


def lancer_scan(cible: str) -> dict:
    """Lance un vrai scan nmap sur une cible autorisée, puis le lit avec lire_scan."""
    cible = verifier_cible(cible)  # brique 3 : AVANT de lancer quoi que ce soit

    config.DOSSIER_SCANS_LIVE.mkdir(parents=True, exist_ok=True)
    nom = cible.replace(".", "_").replace(":", "_")
    sortie = config.DOSSIER_SCANS_LIVE / f"{nom}_{int(time.time())}.xml"

    # Les options sont FIXES : le modèle ne choisit que la cible.
    # On passe une liste (pas de shell=True) : "; rm -rf /" ne serait jamais exécuté.
    commande = ["nmap", "-sV", "-T4", "--top-ports", "100", "-oX", str(sortie), cible]
    try:
        subprocess.run(commande, check=True, capture_output=True, timeout=600)
    except FileNotFoundError:
        raise RuntimeError("nmap n'est pas installé (voir le README)")
    return lire_scan(str(sortie))
