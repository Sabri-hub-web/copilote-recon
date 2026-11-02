# Copilote de recon nmap vérifié

Un petit modèle de langage (Qwen3.5-4B, en local) analyse des scans nmap :
il résume la surface d'attaque et dit par où commencer. On ne lui fait pas
confiance : **le code** lit le vrai scan, bloque les cibles hors périmètre et
refuse toute réponse qui cite un port qui n'est pas réellement ouvert.

Briques couvertes : **1** (outil), **2** (serveur MCP), **3** (règle imposée par le code),
**5** (mémoire), **9** (comparaison mesurée). Les preuves sont dans [EVIDENCE.md](EVIDENCE.md).

> Usage légal uniquement : on ne scanne que sa propre machine, son labo Docker
> et `scanme.nmap.org` (autorisé par nmap). Le code l'impose.

## Architecture

```
            demande
               │
               ▼
   ┌───────────────────────┐   appel d'outil   ┌──────────────────────────┐
   │  agent.py (boucle)    │ ───────────────▶  │ outils_nmap.py           │
   │                       │ ◀───────────────  │  lire_scan / lancer_scan │
   │  Qwen3.5-4B (llm.py)  │   ports VRAIS     │  + garde_fous.py         │
   └──────────┬────────────┘                   └──────────────────────────┘
              │ réponse texte                        ▲ (ou via serveur_mcp.py)
              ▼
   ┌───────────────────────┐
   │ garde_fous.verifier_  │  OK ─▶ réponse montrée + memoire.json
   │ reponse()             │  faux ─▶ 1 correction, puis REJET
   └───────────────────────┘
```

## Installation (clone tout neuf)

Prérequis : Python 3.10+, [Ollama](https://ollama.com/download), et
[nmap](https://nmap.org/download) seulement pour les scans en direct.

### 1. Le modèle

```bash
ollama pull qwen3.5:4b-q4_K_M
```

Fixer la longueur de contexte à 8K **avant** de lancer le serveur Ollama :

```powershell
# Windows (PowerShell) — quitter d'abord Ollama dans la barre des tâches
$env:OLLAMA_CONTEXT_LENGTH = "8192"; ollama serve
```
```bash
# Linux / macOS
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

### 2. Le projet

```powershell
git clone <url-du-depot> copilote-recon
cd copilote-recon
python -m venv .venv
.venv\Scripts\activate          # Linux : source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Vérifier (tests automatiques, sans modèle, ~3 s)

```bash
python -m pytest
```

## Utilisation

```bash
# Analyser un scan existant
python -m copilote "Analyse le scan donnees/scans_bench/scan_06.xml"

# Scanner ta propre machine (nmap requis)
python -m copilote "Scanne 127.0.0.1 et dis-moi par où commencer"

# Le garde-fou en action : refusé, nmap n'est jamais lancé
python -m copilote "Scanne 8.8.8.8"

# Via le serveur MCP (brique 2)
python -m copilote.harness_mcp "Analyse le scan donnees/scans_bench/scan_09.xml"

# Benchmark : Qwen seul vs le système (brique 9, ~30-60 min)
python bench/comparer.py
python bench/comparer.py --lancements 1 --taches 2     # essai rapide
python bench/echecs.py resultats/bench_XXXX.json        # voir les échecs et leurs traces
```

Chaque lancement écrit sa trace complète dans `traces/`.

## Configuration (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Ollama. llama.cpp : `http://localhost:8080/v1` |
| `LLM_MODEL` | `qwen3.5:4b-q4_K_M` | Nom du modèle |
| `LLM_API_KEY` | vide | Seulement pour Cerebras (jamais dans le dépôt) |
| `LLM_TEMPERATURE` | `0.7` | > 0 pour que les 3 lancements varient |
| `SCOPE_EXTRA` | vide | Cibles à toi en plus (ex. l'IP de ta VM), hors dépôt |

Avec llama.cpp au lieu d'Ollama :
`llama-server -m Qwen3.5-4B-Q4_K_M.gguf --port 8080 -c 16384 --jinja`
puis `LLM_BASE_URL=http://localhost:8080/v1`.

## Organisation du dépôt

```
copilote/
  config.py        réglages + périmètre autorisé
  outils_nmap.py   BRIQUE 1  lire_scan(), lancer_scan()
  garde_fous.py    BRIQUE 3  cible, chemin, réponse
  memoire.py       BRIQUE 5  memoire.json
  serveur_mcp.py   BRIQUE 2  serveur MCP
  harness_mcp.py   BRIQUE 2  harness qui l'utilise
  agent.py         la boucle de l'agent + "Qwen seul"
  llm.py           connexion au modèle
donnees/
  generer_scans.py les 10 scans du benchmark et leurs réponses
  scans_bench/     les 10 scans (XML nmap)
bench/
  taches.json      les bonnes réponses
  comparer.py      BRIQUE 9
  echecs.py        affiche les échecs avec leur trace
tests/             pytest (exigence R2)
preuves/           traces retenues pour EVIDENCE.md
ai_log/            journal d'usage de l'IA (exigence R3)
```

Aucune clé, aucun mot de passe ni aucune donnée personnelle dans le dépôt :
`memoire.json`, les scans réels et les traces sont dans `.gitignore`.
