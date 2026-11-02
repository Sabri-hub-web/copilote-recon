"""BRIQUE 2 (suite) — Un harness qui utilise le serveur MCP.

1. Il démarre le serveur MCP (un sous-processus) et s'y connecte.
2. Il demande au serveur la liste de ses outils.
3. Il lance NOTRE agent (copilote/agent.py) avec ces outils : chaque fois que
   Qwen demande un outil, l'appel passe par MCP.
4. Il enregistre la trace dans traces/mcp_<date>.json.

    python -m copilote.harness_mcp "Analyse donnees/scans_bench/scan_01.xml"
    python -m copilote.harness_mcp --sans-llm      (juste un appel MCP, sans Qwen)
"""
import asyncio
import json
import sys
from datetime import datetime

from mcp import ClientSession, StdioServerParameters, stdio_client

from copilote import config
from copilote.agent import analyser
from copilote.llm import ClientLLM


def outil_mcp_vers_format_llm(outil) -> dict:
    """Traduit la description MCP d'un outil vers le format que Qwen comprend."""
    return {"type": "function", "function": {
        "name": outil.name, "description": outil.description or "",
        "parameters": outil.input_schema}}


def lire_resultat_mcp(resultat):
    """Le serveur renvoie du texte JSON : on le retransforme en dict."""
    texte = resultat.content[0].text if resultat.content else "{}"
    if resultat.is_error:                       # le garde-fou a levé une erreur côté serveur
        return {"erreur": f"REFUSÉ par le serveur MCP : {texte}"}
    return json.loads(texte)


async def principal(demande, sans_llm=False):
    parametres = StdioServerParameters(command=sys.executable,
                                       args=["-m", "copilote.serveur_mcp"],
                                       cwd=str(config.RACINE))
    async with stdio_client(parametres) as (lecture, ecriture):
        async with ClientSession(lecture, ecriture) as session:
            await session.initialize()
            outils = (await session.list_tools()).tools
            print("Outils exposés par le serveur MCP :", [o.name for o in outils])

            if sans_llm:  # un appel direct, pour prouver que le serveur répond
                res = await session.call_tool("lire_scan",
                                              {"chemin": "donnees/scans_bench/scan_01.xml"})
                return {"appel": "lire_scan", "resultat": lire_resultat_mcp(res)}

            boucle = asyncio.get_running_loop()

            def executeur_mcp(nom, arguments):
                # L'agent tourne dans un autre thread (il n'est pas "async").
                # On renvoie chaque appel d'outil vers cette boucle, qui parle au serveur.
                futur = asyncio.run_coroutine_threadsafe(session.call_tool(nom, arguments), boucle)
                return lire_resultat_mcp(futur.result())

            return await asyncio.to_thread(
                analyser, demande, ClientLLM(),
                executeur=executeur_mcp,
                outils=[outil_mcp_vers_format_llm(o) for o in outils])


def main():
    args = [a for a in sys.argv[1:] if a != "--sans-llm"]
    sans_llm = "--sans-llm" in sys.argv
    demande = args[0] if args else "Analyse le scan donnees/scans_bench/scan_01.xml"
    resultat = asyncio.run(principal(demande, sans_llm))

    config.DOSSIER_TRACES.mkdir(exist_ok=True)
    fichier = config.DOSSIER_TRACES / f"mcp_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    fichier.write_text(json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultat, indent=2, ensure_ascii=False)[:3000])
    print(f"\nTrace enregistrée : {fichier}")


if __name__ == "__main__":
    main()
