"""Tests de la brique 5 : la mémoire survit à un redémarrage."""
from conftest import FauxLLM, appel_outil, texte

from copilote.agent import analyser
from copilote.memoire import Memoire, estimer_tokens

BONNE = "SSH et HTTP.\nPORTS: 22, 80"


def test_souvenir_apres_redemarrage(tmp_path):
    fichier = tmp_path / "memoire.json"
    m1 = Memoire(fichier)
    m1.enregistrer("172.17.0.2", [80, 22], "SSH et HTTP")
    del m1                                       # "on ferme le programme"

    m2 = Memoire(fichier)                        # "on le relance" : relit le fichier
    assert m2.rappeler("172.17.0.2")["ports_ouverts"] == [22, 80]
    assert "172.17.0.2" in m2.contexte_pour("172.17.0.2")


def test_cible_inconnue(tmp_path):
    m = Memoire(tmp_path / "memoire.json")       # cas limite : fichier inexistant
    assert m.rappeler("10.0.0.1") is None
    assert m.contexte_pour("10.0.0.1") == ""


def test_agent_utilise_la_memoire_entre_deux_sessions(tmp_path, scan_01):
    fichier = tmp_path / "memoire.json"

    # Session 1 : première analyse, rien en mémoire
    llm1 = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(BONNE)])
    r1 = analyser("Analyse " + scan_01, llm1, memoire=Memoire(fichier))
    assert "souvenir" not in r1["trace"][0]["resultat"]
    assert r1["tokens"]["memoire_estimee"] == 0

    # Session 2 : NOUVEL objet Memoire (= redémarrage), même cible
    llm2 = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(BONNE)])
    r2 = analyser("Analyse " + scan_01, llm2, memoire=Memoire(fichier))
    souvenir = r2["trace"][0]["resultat"]["souvenir"]
    assert "[22, 80]" in souvenir
    assert r2["tokens"]["memoire_estimee"] == estimer_tokens(souvenir) > 0   # le coût


def test_reponse_rejetee_pas_memorisee(tmp_path, scan_01):
    fichier = tmp_path / "memoire.json"
    faux = "MySQL.\nPORTS: 3306"
    llm = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(faux), texte(faux)])
    analyser("Analyse " + scan_01, llm, memoire=Memoire(fichier))
    assert Memoire(fichier).rappeler("172.17.0.2") is None   # on ne retient pas du faux
