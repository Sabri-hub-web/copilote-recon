"""Tests de la brique 2 (vrai serveur MCP) et de la notation de la brique 9."""
import asyncio

from bench.comparer import moyenne_ecart, noter, resumer
from copilote.harness_mcp import principal


def test_serveur_mcp_repond_vraiment():
    # Démarre le VRAI serveur MCP dans un sous-processus et appelle lire_scan.
    r = asyncio.run(principal("", sans_llm=True))
    ports = [p["port"] for p in r["resultat"]["ports_ouverts"]]
    assert ports == [22, 80]


def test_serveur_mcp_refuse_une_cible_interdite():
    import sys
    from mcp import ClientSession, StdioServerParameters, stdio_client
    from copilote import config
    from copilote.harness_mcp import lire_resultat_mcp

    async def essai():
        p = StdioServerParameters(command=sys.executable, args=["-m", "copilote.serveur_mcp"],
                                  cwd=str(config.RACINE))
        async with stdio_client(p) as (lecture, ecriture):
            async with ClientSession(lecture, ecriture) as session:
                await session.initialize()
                return lire_resultat_mcp(await session.call_tool("lancer_scan", {"cible": "8.8.8.8"}))

    assert "REFUSÉ" in asyncio.run(essai())["erreur"]


def test_noter():
    vrais = [22, 80]
    assert noter({"statut": "validee", "reponse": "PORTS: 22, 80"}, vrais)["issue"] == "juste"
    n = noter({"statut": "non_verifiee", "reponse": "PORTS: 22, 80, 443"}, vrais)
    assert n == {"issue": "fausse", "inventes": 1, "oublies": 0}
    assert noter({"statut": "rejetee", "reponse": None}, vrais)["issue"] == "rejetee"
    # cas limite : pas de ligne PORTS -> tous les ports sont "oubliés"
    assert noter({"statut": "non_verifiee", "reponse": "bla"}, vrais)["oublies"] == 2


def test_resumer_et_dispersion():
    notes = [{"issue": "juste", "inventes": 0}, {"issue": "fausse", "inventes": 2}]
    assert resumer(notes) == {"taux_juste": 0.5, "taux_fausse": 0.5,
                              "taux_rejetee": 0.0, "ports_inventes": 2}
    assert moyenne_ecart([1, 1, 1]) == "1.00 ± 0.00"
    assert moyenne_ecart([0.5]) == "0.50 ± 0.00"     # cas limite : un seul lancement
