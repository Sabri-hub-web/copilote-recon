"""BRIQUE 3 — Les règles imposées par le CODE (et pas par le prompt).

Trois règles que le système ne doit jamais enfreindre :
  1. Ne jamais scanner une cible hors du périmètre autorisé.
  2. Ne jamais lire un fichier en dehors du dossier "donnees/".
  3. Ne jamais montrer à l'utilisateur une réponse qui cite un port
     qui n'est pas réellement ouvert dans le scan (= hallucination).

Le prompt DEMANDE au modèle de respecter ces règles, mais un modèle peut
désobéir. Ici, c'est du Python : il ne peut pas désobéir.
"""
import ipaddress
import re
from pathlib import Path

from copilote import config


class CibleInterdite(Exception):
    """Levée quand quelqu'un (humain ou modèle) demande une cible interdite."""


class CheminInterdit(Exception):
    """Levée quand on essaie de lire un fichier hors du dossier autorisé."""


# ---------------------------------------------------------------------------
# Règle 1 : le périmètre
# ---------------------------------------------------------------------------
def verifier_cible(cible: str) -> str:
    """Renvoie la cible si elle est autorisée, sinon lève CibleInterdite."""
    cible = str(cible).strip()

    # a) un nom autorisé, écrit exactement (ex. "scanme.nmap.org")
    if cible.lower() in config.NOMS_AUTORISES or cible in config.SCOPE_EXTRA:
        return cible

    # b) sinon ça DOIT être une adresse IP valide.
    #    "127.0.0.1; rm -rf /" ou "-oN /etc/passwd" ne sont pas des IP :
    #    ipaddress lève ValueError -> on refuse. C'est ce qui bloque l'injection.
    try:
        ip = ipaddress.ip_address(cible)
    except ValueError:
        raise CibleInterdite(f"'{cible}' n'est ni une IP valide ni un nom autorisé")

    # c) l'IP doit être dans un des réseaux autorisés
    for reseau in config.RESEAUX_AUTORISES:
        if ip in ipaddress.ip_network(reseau):
            return cible
    raise CibleInterdite(f"{cible} est hors du périmètre autorisé")


# ---------------------------------------------------------------------------
# Règle 2 : on ne lit que dans le dossier donnees/
# ---------------------------------------------------------------------------
def verifier_chemin(chemin: str) -> Path:
    """Renvoie le chemin absolu s'il est DANS donnees/, sinon lève CheminInterdit."""
    dossier = config.DOSSIER_SCANS.resolve()
    p = Path(chemin)
    if not p.is_absolute():
        p = config.RACINE / p
    p = p.resolve()  # resolve() transforme "donnees/../../etc/passwd" en vrai chemin
    if dossier != p and dossier not in p.parents:
        raise CheminInterdit(f"'{chemin}' est hors du dossier {dossier.name}/")
    if p.suffix.lower() != ".xml":
        raise CheminInterdit(f"'{chemin}' n'est pas un fichier .xml")
    return p


# ---------------------------------------------------------------------------
# Règle 3 : la réponse du modèle doit coller au vrai scan
# ---------------------------------------------------------------------------
# "PORTS: 22, 80, 443"  (la dernière ligne qu'on exige du modèle)
_LIGNE_PORTS = re.compile(r"^\W*PORTS\W*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
# "22/tcp" ou "53/udp"
_PORT_SLASH = re.compile(r"\b(\d{1,5})/(?:tcp|udp)\b", re.IGNORECASE)
# "port 22", "Port 3306"
_PORT_MOT = re.compile(r"\bports?\s+(\d{1,5})\b", re.IGNORECASE)


def extraire_ligne_ports(texte: str):
    """Lit la ligne 'PORTS: ...'. Renvoie un set d'entiers, ou None si absente."""
    trouvailles = _LIGNE_PORTS.findall(texte)
    if not trouvailles:
        return None
    derniere = trouvailles[-1]  # s'il y en a plusieurs, on prend la dernière
    return {int(n) for n in re.findall(r"\d{1,5}", derniere)}


def ports_cites(texte: str) -> set:
    """Tous les ports mentionnés dans le texte libre ('22/tcp', 'port 80').

    On retire SEULEMENT la dernière ligne 'PORTS:' (celle déjà vérifiée à part).
    Une autre ligne qui commence par 'Ports:' plus haut reste vérifiée :
    sinon le modèle pourrait y cacher un port inventé.
    """
    lignes_ports = list(_LIGNE_PORTS.finditer(texte))
    if lignes_ports:
        derniere = lignes_ports[-1]
        sans_ligne_finale = texte[:derniere.start()] + texte[derniere.end():]
    else:
        sans_ligne_finale = texte
    trouves = _PORT_SLASH.findall(sans_ligne_finale) + _PORT_MOT.findall(sans_ligne_finale)
    return {int(n) for n in trouves}


def verifier_reponse(texte: str, scan: dict) -> list:
    """Compare la réponse du modèle au scan. Renvoie la liste des problèmes.

    Liste vide = réponse valide.
    """
    vrais = {p["port"] for p in scan["ports_ouverts"]}
    problemes = []

    annonces = extraire_ligne_ports(texte)
    if annonces is None:
        problemes.append("la ligne finale 'PORTS: ...' est absente")
    else:
        for port in sorted(annonces - vrais):
            problemes.append(f"port {port} annoncé comme ouvert mais il ne l'est pas dans le scan")
        for port in sorted(vrais - annonces):
            problemes.append(f"port {port} ouvert dans le scan mais oublié dans la ligne PORTS")

    for port in sorted(ports_cites(texte) - vrais):
        problemes.append(f"port {port} cité dans le texte mais il n'est pas ouvert dans le scan")

    return problemes
