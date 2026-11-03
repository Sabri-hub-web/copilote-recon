# Notes de séance

## Séance 1 — 2 novembre 2026 (soir) — choix du sujet et construction

**Ce que j'ai décidé.** Sujet : un copilote de recon nmap, en lien avec mon projet de
clinique de pentest. Briques 1, 2, 3, 5 et 9, choisies parce que je peux les expliquer.
Cibles limitées à ma machine, mon labo Docker et scanme.nmap.org.

**Ce que l'IA a fait.** Claude a proposé le découpage en fichiers et écrit le code, les
tests, le README et la structure de EVIDENCE.md.

**Gardé tel quel.**
- `outils_nmap.py`, `memoire.py`, `llm.py` : [À COMPLÉTER : ce que j'ai relu et compris]

**Corrigé (quoi, pourquoi).**
- `garde_fous.ports_cites()` : en testant avec un faux modèle, une ligne « Ports: ... »
  en haut de la réponse cachait un port inventé (9999). Corrigé pour ne retirer que la
  dernière ligne `PORTS:`, avec un test de non-régression.
- Serveur MCP : un refus du garde-fou remontait en trace d'erreur illisible.
  Il renvoie maintenant `{"erreur": "REFUSÉ ..."}`.

**Prompt réécrit (quelle ligne, pourquoi).**
- `PROMPT_SYSTEME` : ajout de « Termine OBLIGATOIREMENT par une ligne PORTS: ... »,
  pour que le code puisse vérifier la réponse automatiquement.

## Séance 2 — 3 novembre 2026 — installation, lancement sur Qwen, compréhension

**Installation.** Ollama et nmap installés sur D: (disque C: plein). Qwen tourne à 100 % GPU,
contexte 8192. 51 tests passent sous Windows.

**Premiers vrais lancements.** Analyse de scan_01 validée. « Scanne 8.8.8.8 » refusé par le
garde-fou ; Qwen a ensuite essayé 127.0.0.1 de lui-même (autorisé). Scan réel de ma machine :
ports 135 et 445, ports justes, mais conseil faux (« évasion de conteneurs » pour SMB).

**Corrigé à la main.** `__main__.py` : l'erreur « nmap n'est pas installé » s'affichait avec
l'étiquette `[GARDE-FOU]` ; distinction ajoutée entre `[GARDE-FOU]` (refus) et `[ERREUR OUTIL]`.

**Benchmark.** Série facile : 100 % de réponses justes pour les deux, effet plafond.
Décision : garder ce résultat et ajouter une série difficile (scan_11 à scan_20).
[À COMPLÉTER : résultat de la série difficile]
