"""Tests de la brique 1 : lire_scan doit trouver exactement les ports ouverts."""
import json
from pathlib import Path

import pytest

from copilote import config
from copilote.outils_nmap import lire_scan

TACHES = json.loads((Path(__file__).resolve().parent.parent / "bench" / "taches.json")
                    .read_text(encoding="utf-8"))


def test_scan_simple(scan_01):
    resultat = lire_scan(scan_01)
    assert resultat["cible"] == "172.17.0.2"
    assert [p["port"] for p in resultat["ports_ouverts"]] == [22, 80]   # 443 est "closed"
    assert resultat["ports_ouverts"][0]["service"] == "ssh"
    assert resultat["ports_ouverts"][0]["produit"] == "OpenSSH 8.9p1 Ubuntu 3ubuntu0.6"


def test_open_filtered_ne_compte_pas():
    # scan_08 : 161/udp et 500/udp sont "open|filtered" -> pas ouverts
    ports = [p["port"] for p in lire_scan("donnees/scans_bench/scan_08.xml")["ports_ouverts"]]
    assert ports == [22, 53, 123]


@pytest.mark.parametrize("tache", TACHES, ids=[t["id"] for t in TACHES])
def test_les_10_scans_du_bench(tache):
    # La vérité de taches.json a été écrite à la main (generer_scans.py) :
    # si lire_scan se trompe sur un seul scan, ce test échoue.
    ports = [p["port"] for p in lire_scan(tache["fichier"])["ports_ouverts"]]
    assert ports == tache["ports_ouverts"]


def test_cas_limite_aucun_hote(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DOSSIER_SCANS", tmp_path)
    vide = tmp_path / "vide.xml"
    vide.write_text('<?xml version="1.0"?><nmaprun><runstats/></nmaprun>', encoding="utf-8")
    assert lire_scan(str(vide)) == {"cible": None, "ports_ouverts": []}


def test_cas_limite_aucun_port_ouvert(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DOSSIER_SCANS", tmp_path)
    f = tmp_path / "ferme.xml"
    f.write_text('<nmaprun><host><address addr="127.0.0.1"/><ports>'
                 '<port protocol="tcp" portid="80"><state state="closed"/></port>'
                 '</ports></host></nmaprun>', encoding="utf-8")
    assert lire_scan(str(f)) == {"cible": "127.0.0.1", "ports_ouverts": []}
