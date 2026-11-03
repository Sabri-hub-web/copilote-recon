# Notes de séance (journal d'usage de l'IA, exigence R3)

Outil d'IA utilisé : **Claude** (claude.ai), en une longue conversation du 2 au 4 novembre 2026,
exportée dans `ai_log/conversations/`.

Comment j'ai travaillé : je ne suis pas très à l'aise avec le code. J'ai donc choisi le sujet
et les briques, Claude a écrit le code, et je l'ai fait tourner sur mes machines puis étudié
fichier par fichier, en réexpliquant chaque partie avec mes mots jusqu'à pouvoir la défendre.
Chaque séance indique : ce que j'ai décidé, ce qui a été gardé tel quel, ce qui a été corrigé
(quoi, pourquoi), et les prompts réécrits.

---

## Séance 1 — 2 novembre 2026 (soir) — choix du sujet et construction

**Ce que j'ai décidé.**
- Un sujet personnel, en lien avec mon projet de clinique de pentest : un copilote qui analyse
  des scans nmap avec Qwen, sans lui faire confiance.
- Briques 1, 2, 3, 5 et 9 : toutes côté agents et mesure, parce que ce sont celles que je peux
  expliquer. J'ai écarté les briques 6, 7 et 8 (statistiques et ML écrits à la main).
- Cibles limitées à ma machine, mon labo Docker et scanme.nmap.org (légalité).

**Ce que l'IA a fait.** Claude a proposé le découpage en fichiers et écrit le code, les tests,
le README, la structure de EVIDENCE.md et les 10 premiers scans du benchmark.

**Corrigé pendant la construction (trouvé par Claude en testant avec un faux modèle).**
- `garde_fous.ports_cites()` : une ligne « Ports: ... » en haut de la réponse était prise pour
  la ligne finale et ignorée, donc un port inventé (9999) passait le contrôle. Corrigé pour ne
  retirer que la **dernière** ligne `PORTS:`, avec le test `test_port_cache_dans_une_autre_ligne_ports`.
- `serveur_mcp.py` : un refus du garde-fou remontait en longue trace d'erreur illisible. Le
  serveur renvoie maintenant `{"erreur": "REFUSÉ ..."}`.
- `llm.py` : quand Ollama n'est pas lancé, le message d'erreur est court et dit quoi faire.

**Prompt réécrit (quelle ligne, pourquoi).**
- `PROMPT_SYSTEME`, dernière consigne : « Termine OBLIGATOIREMENT par une ligne PORTS: ... ».
  Sans ligne au format fixe, une réponse en texte libre est impossible à vérifier
  automatiquement.
- `PROMPT_SEUL` (référence de la brique 9) : même consigne mais sans outil, pour que la
  comparaison Qwen seul / mon système soit équitable.

---

## Séance 2 — 3 novembre 2026 — installation, vrais lancements, benchmark, compréhension

**Installation sur ma tour (Windows, RTX 3050).** Ollama et nmap installés sur D: parce que C:
était plein (premières installations échouées). Qwen tourne à 100 % GPU, contexte 8192.
Les tests passent sous Windows.

**Premiers vrais lancements.**
- `scan_01` : réponse validée du premier coup.
- « Scanne 8.8.8.8 » : refusé par le garde-fou. Qwen a ensuite essayé **de lui-même**
  `127.0.0.1` (autorisé), ce qui montre pourquoi le périmètre doit être dans le code.
- Scan réel de ma machine : ports 135 et 445, justes, mais un conseil faux (« évasion de
  conteneurs » pour SMB). Ce que mon vérificateur ne contrôle pas : les conseils.

**Corrigé (quoi, pourquoi).** `__main__.py` : l'erreur « nmap n'est pas installé »
s'affichait avec l'étiquette `[GARDE-FOU]`, alors que ce n'était pas un refus. Distinction
ajoutée entre `[GARDE-FOU]` (refus) et `[ERREUR OUTIL]`.

**Benchmark : ma décision après le premier résultat.**
- Série facile : 100 % de réponses justes pour Qwen seul **et** pour mon système. Le test ne
  sépare rien : effet plafond.
- Décision : **garder ce résultat tel quel** dans EVIDENCE.md, et ajouter une série difficile
  (scan_11 à scan_20 : 30 à 46 ports ouverts, leurres, pièges TCP/UDP). J'écris dans
  EVIDENCE.md qu'elle a été ajoutée après coup.
- Série difficile : Qwen seul 0 %, mon système 100 %. Diagnostic sur les traces (petits scripts
  écrits par Claude, lancés par moi) : 28 réponses sur 30 de Qwen seul sont **vides**, parce que
  le XML (≈ 4 200 tokens) et sa réflexion remplissent les 8 192 tokens du contexte. Mon système
  a corrigé 6 réponses de Qwen, dont un port 3389 complètement inventé (scan_12).

**Preuves produites.** Briques 2 (appel via MCP) et 5 (mémoire : 0 puis 32 tokens estimés,
+69 tokens mesurés par Ollama) avec le vrai Qwen, copiées dans `preuves/`. Projet publié sur
GitHub, puis testé sur un **clone tout neuf** : tests verts et analyse validée (R1, R2).

**Ce que j'ai étudié (le code gardé tel quel, que je sais maintenant expliquer).**
- nmap : ports, états `open` / `closed` / `filtered`, `-sV` et les versions, CVE (vsftpd 2.3.4,
  EternalBlue sur SMB/445).
- `outils_nmap.py` : `lire_scan` ne garde que `state == "open"` ; `int()` pour trier et
  comparer ; `lancer_scan` vérifie la cible avant nmap, options fixes, liste sans shell.
- `garde_fous.py` : liste blanche d'IP avec `ipaddress` (l'injection n'est pas une IP) ;
  `resolve()` contre la traversée de répertoire ; différences d'ensembles pour les ports
  inventés (`annonces - vrais`) et oubliés (`vrais - annonces`). Je confondais les deux
  soustractions au début.
- `agent.py` : la boucle (Qwen demande, le code exécute et garde le vrai scan comme référence,
  vérifie, une seule correction, sinon rejet). C'est la partie que j'ai eu le plus de mal à
  comprendre : il m'a fallu deux explications.
- `memoire.py`, `serveur_mcp.py`, `harness_mcp.py`.

---

## Séance 3 — 4 novembre 2026 (nuit) — portable et répétition de la démo

**Contexte.** La soutenance est en présentiel : je passe sur mon portable (i5-1335U, 16 Go,
pas de carte graphique dédiée). Installation depuis GitHub : tests verts.

**Mesure.** Une analyse prend **176 s** sur le processeur du portable, contre 20 à 40 s sur
le GPU de ma tour.

**Mes décisions.**
- **Pas de VM Scaleway** pour la démo, alors que j'en ai une : le sujet demande que le modèle
  tourne sur mon propre ordinateur, et mon portable en est capable, même lentement.
- **Démo réorganisée** : je lance l'analyse en premier et je présente le reste pendant qu'elle
  tourne. `OLLAMA_KEEP_ALIVE=60m` pour garder Qwen chargé.
- Pour la brique 3, je montre `pytest tests/test_garde_fous.py -v` (instantané) plutôt que
  « Scanne 8.8.8.8 » avec Qwen, qui ferait plusieurs tours et prendrait plusieurs minutes sur
  le processeur. Le refus avec le vrai Qwen est déjà dans EVIDENCE.md.

**Erreur faite pendant la répétition.** Lancer `pytest` dans un nouvel onglet sans activer
`.venv` : « No module named pytest ». À chaque nouvel onglet : `cd` puis `activate`.
