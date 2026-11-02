"""Le cœur du système : la boucle de l'agent.

Déroulé d'une analyse :
  1. On envoie au modèle la demande + la liste des outils.
  2. Si le modèle demande un outil, NOTRE code l'exécute (avec les garde-fous)
     et on lui renvoie le résultat. On recommence.
  3. Quand le modèle répond en texte, NOTRE code vérifie sa réponse contre le
     vrai scan (brique 3).
       - valide       -> on la montre à l'utilisateur ("validee")
       - pas valide   -> on lui renvoie ses erreurs, UNE seule seconde chance
       - encore faux  -> on refuse de montrer la réponse ("rejetee")
"""
import json

from copilote import config
from copilote.garde_fous import CheminInterdit, CibleInterdite, verifier_reponse
from copilote.llm import nettoyer
from copilote.memoire import estimer_tokens
from copilote.outils_nmap import lancer_scan, lire_scan

PROMPT_SYSTEME = """Tu es un assistant de reconnaissance pour un pentest autorisé, en laboratoire.
Pour connaître les ports d'une machine, tu DOIS appeler un outil :
- lire_scan(chemin) pour un fichier de scan nmap déjà fait,
- lancer_scan(cible) pour scanner une cible.
N'invente jamais : ne parle QUE des ports ouverts renvoyés par l'outil.
Réponds en français, en 2 parties courtes :
1. Surface d'attaque : chaque port ouvert, son service et sa version.
2. Par où commencer : les 2 ou 3 services à creuser en premier, et pourquoi.
Termine OBLIGATOIREMENT par une dernière ligne exactement de cette forme :
PORTS: <les numéros des ports ouverts séparés par des virgules>"""

# Même consigne, sans outil : utilisé pour "Qwen seul" (référence de la brique 9).
PROMPT_SEUL = """Tu es un assistant de reconnaissance pour un pentest autorisé, en laboratoire.
On te donne un scan nmap. Ne parle QUE des ports ouverts (state="open").
Réponds en français, en 2 parties courtes :
1. Surface d'attaque : chaque port ouvert, son service et sa version.
2. Par où commencer : les 2 ou 3 services à creuser en premier, et pourquoi.
Termine OBLIGATOIREMENT par une dernière ligne exactement de cette forme :
PORTS: <les numéros des ports ouverts séparés par des virgules>"""

# La description des outils, dans le format que le modèle comprend.
OUTILS = [
    {"type": "function", "function": {
        "name": "lire_scan",
        "description": "Lit un fichier XML de scan nmap (dossier donnees/) et renvoie les ports ouverts.",
        "parameters": {"type": "object",
                       "properties": {"chemin": {"type": "string",
                                                 "description": "ex. donnees/scans_bench/scan_01.xml"}},
                       "required": ["chemin"]}}},
    {"type": "function", "function": {
        "name": "lancer_scan",
        "description": "Lance un scan nmap sur une cible autorisée et renvoie les ports ouverts.",
        "parameters": {"type": "object",
                       "properties": {"cible": {"type": "string",
                                                "description": "adresse IP ou nom, ex. 127.0.0.1"}},
                       "required": ["cible"]}}},
]


def executer_outil(nom: str, arguments: dict) -> dict:
    """Exécute l'outil demandé par le modèle. Les garde-fous sont DANS les outils."""
    if nom == "lire_scan":
        return lire_scan(arguments["chemin"])
    if nom == "lancer_scan":
        return lancer_scan(arguments["cible"])
    raise ValueError(f"outil inconnu : {nom}")


def analyser(demande: str, llm, memoire=None, executeur=executer_outil,
             outils=OUTILS, max_tours: int = 6) -> dict:
    """Lance l'agent sur une demande. Renvoie un dict avec statut, réponse et trace."""
    messages = [{"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": demande}]
    trace = []                     # tout ce qui se passe, pour EVIDENCE.md
    scan = None                    # le dernier scan VRAI lu par nos outils
    deja_corrige = False
    problemes = ["le modèle n'a jamais donné de réponse finale"]
    tokens = {"prompt": 0, "reponse": 0, "memoire_estimee": 0}

    for tour in range(max_tours):
        message, usage = llm.discuter(messages, outils)
        tokens["prompt"] += usage.get("prompt_tokens", 0)
        tokens["reponse"] += usage.get("completion_tokens", 0)
        appels = message.get("tool_calls") or []

        # ---------- Cas 1 : le modèle veut utiliser un outil ----------
        if appels:
            messages.append({"role": "assistant", "content": message.get("content") or "",
                             "tool_calls": appels})
            for appel in appels:
                nom = appel["function"]["name"]
                args = appel["function"].get("arguments") or {}
                if isinstance(args, str):           # souvent du JSON en texte
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                try:
                    resultat = executeur(nom, args)
                    if isinstance(resultat, dict) and "ports_ouverts" in resultat:
                        scan = resultat
                        # Brique 5 : on ajoute le souvenir de cette cible
                        if memoire is not None and resultat.get("cible"):
                            souvenir = memoire.contexte_pour(resultat["cible"])
                            if souvenir:
                                resultat = {**resultat, "souvenir": souvenir}
                                tokens["memoire_estimee"] += estimer_tokens(souvenir)
                except (CibleInterdite, CheminInterdit) as e:
                    resultat = {"erreur": f"REFUSÉ par le garde-fou : {e}"}
                except (KeyError, ValueError, OSError, RuntimeError) as e:
                    resultat = {"erreur": f"{type(e).__name__} : {e}"}
                trace.append({"tour": tour, "outil": nom, "arguments": args, "resultat": resultat})
                messages.append({"role": "tool", "tool_call_id": appel.get("id", nom),
                                 "content": json.dumps(resultat, ensure_ascii=False)})
            continue

        # ---------- Cas 2 : le modèle répond en texte ----------
        texte = nettoyer(message.get("content"))
        trace.append({"tour": tour, "reponse_modele": texte})

        if scan is None:
            # Il répond sans avoir lu de scan : impossible à vérifier.
            problemes = ["aucun scan n'a été lu par un outil : appelle lire_scan ou lancer_scan"]
        else:
            problemes = verifier_reponse(texte, scan)
        trace.append({"tour": tour, "verification": problemes or "OK"})

        if not problemes:
            if memoire is not None and scan.get("cible"):
                memoire.enregistrer(scan["cible"], [p["port"] for p in scan["ports_ouverts"]], texte)
            return {"statut": "validee", "reponse": texte, "problemes": [],
                    "scan": scan, "trace": trace, "tokens": tokens}

        if deja_corrige:
            break                  # deuxième réponse fausse : on arrête
        if scan is not None:       # la seconde chance ne compte qu'une fois le scan lu
            deja_corrige = True
        messages.append({"role": "assistant", "content": texte})
        messages.append({"role": "user", "content":
                         "Ta réponse a été refusée par le vérificateur :\n- "
                         + "\n- ".join(problemes)
                         + "\nCorrige-la en t'appuyant uniquement sur le résultat de l'outil."})

    return {"statut": "rejetee", "reponse": None, "problemes": problemes,
            "scan": scan, "trace": trace, "tokens": tokens}


def modele_seul(chemin: str, llm) -> dict:
    """La RÉFÉRENCE pour la brique 9 : Qwen seul, sans outil ni vérification.

    On lui colle le fichier XML brut dans le prompt et on prend sa réponse telle quelle.
    """
    xml = (config.RACINE / chemin).read_text(encoding="utf-8")
    messages = [{"role": "system", "content": PROMPT_SEUL},
                {"role": "user", "content": f"Voici le scan nmap :\n\n{xml}\n\nQuels ports sont ouverts "
                                            "et par où commencer ?"}]
    message, usage = llm.discuter(messages)
    texte = nettoyer(message.get("content"))
    return {"statut": "non_verifiee", "reponse": texte,
            "trace": [{"reponse_modele": texte}],
            "tokens": {"prompt": usage.get("prompt_tokens", 0),
                       "reponse": usage.get("completion_tokens", 0)}}
