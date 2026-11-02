"""BRIQUE 2 — Mon propre serveur MCP.

Il expose les deux mêmes outils (lire_scan, lancer_scan) via le protocole MCP.
N'importe quel "harness" compatible MCP peut alors les utiliser :
notre harness (copilote/harness_mcp.py), mais aussi Claude Desktop, Pi, etc.

Lancement manuel (il attend des messages sur l'entrée standard) :
    python -m copilote.serveur_mcp
"""
from mcp.server.mcpserver import MCPServer

from copilote import outils_nmap
from copilote.garde_fous import CheminInterdit, CibleInterdite

serveur = MCPServer("copilote-recon")


@serveur.tool()
def lire_scan(chemin: str) -> dict:
    """Lit un fichier XML de scan nmap (dossier donnees/) et renvoie les ports ouverts."""
    try:
        return outils_nmap.lire_scan(chemin)   # mêmes garde-fous que sans MCP
    except CheminInterdit as e:
        return {"erreur": f"REFUSÉ par le garde-fou : {e}"}


@serveur.tool()
def lancer_scan(cible: str) -> dict:
    """Lance un scan nmap sur une cible autorisée et renvoie les ports ouverts."""
    try:
        return outils_nmap.lancer_scan(cible)
    except CibleInterdite as e:
        return {"erreur": f"REFUSÉ par le garde-fou : {e}"}


if __name__ == "__main__":
    serveur.run()   # transport "stdio" par défaut
