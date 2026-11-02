"""Tests de la brique 3 : on ESSAIE d'enfreindre les règles, et on doit être bloqué."""
import subprocess

import pytest

from copilote.garde_fous import (CheminInterdit, CibleInterdite, verifier_chemin,
                                 verifier_cible, verifier_reponse)
from copilote.outils_nmap import lancer_scan, lire_scan

# ---------- Règle 1 : le périmètre ----------

@pytest.mark.parametrize("cible", ["127.0.0.1", "172.17.0.2", "localhost", "scanme.nmap.org"])
def test_cibles_autorisees(cible):
    assert verifier_cible(cible) == cible


@pytest.mark.parametrize("cible", [
    "8.8.8.8",                    # Internet : interdit
    "192.168.1.1",                # le réseau de quelqu'un d'autre
    "google.com",                 # nom non autorisé
    "127.0.0.1; rm -rf /",        # tentative d'injection de commande
    "-oN /etc/passwd",            # tentative d'injection d'option nmap
    "127.0.0.1 8.8.8.8",          # deux cibles d'un coup
    "",                           # cas limite : vide
])
def test_cibles_interdites(cible):
    with pytest.raises(CibleInterdite):
        verifier_cible(cible)


def test_lancer_scan_hors_perimetre_ne_lance_jamais_nmap(monkeypatch):
    # Si nmap était lancé, ce faux subprocess.run ferait échouer le test.
    def interdit(*a, **k):
        raise AssertionError("nmap a été lancé alors que la cible est interdite !")
    monkeypatch.setattr(subprocess, "run", interdit)
    with pytest.raises(CibleInterdite):
        lancer_scan("8.8.8.8")


# ---------- Règle 2 : lire seulement dans donnees/ ----------

@pytest.mark.parametrize("chemin", [
    "../../../../etc/passwd",
    "donnees/../../secret.xml",
    "/etc/hosts.xml",
    "donnees/generer_scans.py",   # dans le dossier, mais pas un .xml
])
def test_chemins_interdits(chemin):
    with pytest.raises(CheminInterdit):
        verifier_chemin(chemin)
    with pytest.raises(CheminInterdit):
        lire_scan(chemin)


# ---------- Règle 3 : pas de port inventé ----------

SCAN = {"cible": "172.17.0.2", "ports_ouverts": [
    {"port": 22, "protocole": "tcp", "service": "ssh", "produit": ""},
    {"port": 80, "protocole": "tcp", "service": "http", "produit": ""}]}


def test_reponse_correcte_acceptee():
    rep = "Le port 22 (SSH) et 80/tcp (HTTP) sont ouverts.\nPORTS: 22, 80"
    assert verifier_reponse(rep, SCAN) == []


def test_port_invente_dans_la_ligne_ports():
    probs = verifier_reponse("SSH et HTTP.\nPORTS: 22, 80, 3306", SCAN)
    assert any("3306" in p for p in probs)


def test_port_invente_dans_le_texte():
    probs = verifier_reponse("Commence par MySQL sur le port 3306.\nPORTS: 22, 80", SCAN)
    assert any("3306" in p for p in probs)


def test_port_oublie():
    probs = verifier_reponse("Seulement SSH.\nPORTS: 22", SCAN)
    assert any("80" in p and "oublié" in p for p in probs)


def test_port_cache_dans_une_autre_ligne_ports():
    # Bug trouvé pendant le développement : une ligne "Ports: ..." en haut de la
    # réponse était ignorée, donc le port 9999 inventé passait le contrôle.
    probs = verifier_reponse("Ports: 22, 80 et port 9999\nPORTS: 22, 80", SCAN)
    assert any("9999" in p for p in probs)


def test_ligne_ports_absente():
    assert verifier_reponse("Le port 22 est ouvert.", SCAN) != []


def test_ligne_ports_en_markdown():
    assert verifier_reponse("Résumé.\n**PORTS:** 22, 80", SCAN) == []
