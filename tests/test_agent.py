"""Tests de la boucle de l'agent, avec un FAUX modèle aux réponses connues."""
import subprocess

from conftest import FauxLLM, appel_outil, texte

from copilote.agent import analyser

BONNE = "1. SSH (22) et HTTP (80/tcp, Apache 2.4.52).\n2. Commence par le web.\nPORTS: 22, 80"
HALLUCINEE = "Il y a SSH, HTTP et MySQL sur le port 3306.\nPORTS: 22, 80, 3306"


def test_cas_normal_reponse_validee(scan_01):
    llm = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(BONNE)])
    r = analyser("Analyse " + scan_01, llm)
    assert r["statut"] == "validee"
    assert r["reponse"] == BONNE
    assert r["trace"][0]["outil"] == "lire_scan"          # la trace garde l'appel d'outil
    assert r["tokens"]["prompt"] == 200                   # 2 appels × 100 tokens


def test_hallucination_corrigee_au_second_essai(scan_01):
    llm = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(HALLUCINEE), texte(BONNE)])
    r = analyser("Analyse " + scan_01, llm)
    assert r["statut"] == "validee"
    # le modèle a bien reçu la liste de ses erreurs
    dernier_message = llm.recus[-1][-1]["content"]
    assert "3306" in dernier_message and "refusée" in dernier_message


def test_hallucination_deux_fois_reponse_rejetee(scan_01):
    llm = FauxLLM([appel_outil("lire_scan", chemin=scan_01), texte(HALLUCINEE), texte(HALLUCINEE)])
    r = analyser("Analyse " + scan_01, llm)
    assert r["statut"] == "rejetee"
    assert r["reponse"] is None                            # rien de faux n'est montré
    assert any("3306" in p for p in r["problemes"])


def test_reponse_sans_avoir_lu_le_scan_est_refusee(scan_01):
    # Le modèle répond direct, sans outil : invérifiable -> on lui demande l'outil.
    llm = FauxLLM([texte(BONNE), appel_outil("lire_scan", chemin=scan_01), texte(BONNE)])
    r = analyser("Analyse " + scan_01, llm)
    assert r["statut"] == "validee"
    assert "aucun scan" in llm.recus[1][-1]["content"]


def test_le_modele_demande_une_cible_interdite(monkeypatch):
    # Même si le MODÈLE demande de scanner Internet, le code refuse.
    def interdit(*a, **k):
        raise AssertionError("nmap lancé sur une cible interdite !")
    monkeypatch.setattr(subprocess, "run", interdit)
    llm = FauxLLM([appel_outil("lancer_scan", cible="8.8.8.8"),
                   texte("Je ne peux pas scanner cette cible."),
                   texte("Désolé."), texte("Désolé."), texte("Désolé."), texte("Désolé.")])
    r = analyser("Scanne 8.8.8.8", llm)
    assert "REFUSÉ" in r["trace"][0]["resultat"]["erreur"]
    assert r["statut"] == "rejetee"


def test_le_modele_essaie_de_lire_un_fichier_systeme():
    llm = FauxLLM([appel_outil("lire_scan", chemin="../../../etc/passwd")] + [texte("?")] * 5)
    r = analyser("Lis /etc/passwd", llm)
    assert "REFUSÉ" in r["trace"][0]["resultat"]["erreur"]
