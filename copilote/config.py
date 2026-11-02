"""Réglages du projet, lus dans les variables d'environnement.

On ne met JAMAIS de clé d'API ici : elle vient de l'environnement (exigence R1).
"""
import os
from pathlib import Path

# Dossier racine du projet (le dossier qui contient "copilote/")
RACINE = Path(__file__).resolve().parent.parent

# --- Le modèle de langage -------------------------------------------------
# Par défaut : Ollama sur ta machine, qui parle le même "langage" que l'API OpenAI.
#   - Ollama     : http://localhost:11434/v1   modèle qwen3.5:4b-q4_K_M
#   - llama.cpp  : http://localhost:8080/v1    (le nom du modèle est ignoré)
#   - Cerebras   : https://api.cerebras.ai/v1  modèle qwen-3.8-27b + LLM_API_KEY
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5:4b-q4_K_M")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
# Température > 0 : deux lancements ne donnent pas la même réponse,
# c'est pour ça que la brique 9 fait 3 lancements et mesure la dispersion.
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "300"))  # secondes

# --- Les dossiers ---------------------------------------------------------
DOSSIER_SCANS = RACINE / "donnees"            # l'agent ne peut lire QUE là-dedans
DOSSIER_SCANS_LIVE = RACINE / "donnees" / "scans_live"
DOSSIER_TRACES = RACINE / "traces"
FICHIER_MEMOIRE = RACINE / "memoire.json"

# --- Le périmètre (brique 3) ---------------------------------------------
# Les seules cibles qu'on a le droit de scanner.
#   127.0.0.0/8     : ta propre machine
#   172.16.0.0/12   : les conteneurs Docker de ton labo
#   scanme.nmap.org : serveur mis à disposition par nmap POUR être scanné
RESEAUX_AUTORISES = ["127.0.0.0/8", "172.16.0.0/12"]
NOMS_AUTORISES = ["localhost", "scanme.nmap.org"]
# Pour ajouter une machine à toi (ex. ta VM) SANS la mettre dans le dépôt :
#   SCOPE_EXTRA="51.15.x.x"   (plusieurs cibles séparées par des virgules)
SCOPE_EXTRA = [c.strip() for c in os.environ.get("SCOPE_EXTRA", "").split(",") if c.strip()]
