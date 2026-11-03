# Résumé de la conversation avec Claude (2 au 4 novembre 2026)

L'export complet et brut de la conversation est dans `conversation_claude.pdf`, dans ce même
dossier. Ce résumé sert seulement à s'y repérer : il ne le remplace pas.

Outil : Claude (claude.ai). Une seule conversation, découpée ici par étapes.

---

## 1. Choix du sujet (2 novembre, soir)

- Je voulais un projet **personnel**, facile à expliquer. Claude m'a proposé 4 idées ; j'ai
  choisi le **copilote de recon nmap**, en lien avec mon projet de clinique de pentest.
- Après lecture du sujet, choix des briques **1, 2, 3, 5, 9**, parce que je peux les expliquer.
  J'ai dit que je n'étais pas très à l'aise avec le code : la méthode retenue a été « Claude
  écrit, je lis, je réexplique avec mes mots ».
- Premier mini-cours de cyber : recon, ports, états `open` / `closed` / `filtered`, versions,
  sortie XML, périmètre légal (article 323-1 du Code pénal), hallucination.

## 2. Construction du projet par Claude (2 novembre, soir)

- Code, tests, README, EVIDENCE.md, 10 scans de benchmark.
- Claude a testé le code avec un faux modèle et a trouvé un **bug** dans le vérificateur (port
  inventé caché dans une ligne « Ports: »), corrigé avec un test.
- Remis sous forme de zip, avec un guide de soutenance.

## 3. Installation sur ma tour (3 novembre, après-midi)

- Plusieurs blocages réglés pas à pas : erreurs de hachage de winget, **disque C: plein**
  (Ollama et Qwen installés sur D:), zip introuvable, `.venv` créé au mauvais endroit,
  installation de nmap qui plantait (Zenmap décoché, Npcap gardé).
- Qwen3.5-4B tourne à 100 % sur la RTX 3050, contexte 8192. Tests verts.

## 4. Premiers vrais lancements

- Analyse validée de `scan_01`.
- « Scanne 8.8.8.8 » refusé ; Qwen a essayé 127.0.0.1 tout seul.
- Scan réel de ma machine (135, 445) : ports justes, mais conseil faux sur SMB.

## 5. Leçons et quiz (3 novembre, après-midi et soir)

À chaque leçon, Claude posait des questions, je répondais avec mes mots, puis il corrigeait.

| Leçon | Contenu | Ce que j'ai mal compris au début (corrigé) |
|---|---|---|
| 1. nmap | Ports, états, `-sV`, `-oX`, légalité | — |
| CVE | Versions vulnérables : vsftpd 2.3.4, Apache 2.4.49, EternalBlue (SMB/445) | Je n'avais pas compris le lien entre version et faille : réexpliqué avec l'image d'une serrure |
| 2. Vue d'ensemble | Le rôle de chaque fichier | — |
| 3. `outils_nmap.py` | `lire_scan`, `continue`, `int()`, `lancer_scan` | J'avais mélangé `lire_scan` et `lancer_scan` dans la question « que se passe-t-il avec 8.8.8.8 » |
| 4. `garde_fous.py` | Liste blanche d'IP, `resolve()`, différences d'ensembles | J'avais inversé `annonces - vrais` et `vrais - annonces` ; je croyais que le code interdisait les `..` (en fait il calcule le vrai chemin) |
| 5. `agent.py` | La boucle de l'agent | Pas compris à la première explication ; réexpliqué avec « le stagiaire et le chef » puis un exercice à trous |
| 6. `memoire.py` | `memoire.json`, coût en tokens | — |
| 7. MCP | `serveur_mcp.py`, `harness_mcp.py` | — |
| R1 à R4 | Les 4 exigences et le test sur clone neuf | — |

## 6. Benchmark (brique 9) et décision « effet plafond »

- Série facile : Qwen seul et mon système à 100 %. Claude a expliqué l'**effet plafond**.
- Décision : garder ce résultat et ajouter une **série difficile**, en le disant dans EVIDENCE.md.
- Série difficile : Qwen seul 0 %, mon système 100 %. Diagnostic avec deux petits scripts lancés
  par moi : contexte saturé (8 188 tokens en moyenne sur 8 192), 28 réponses vides sur 30, et
  6 corrections dont un port 3389 inventé.

## 7. Preuves, GitHub, clone neuf (3 novembre, soir)

- Preuves des briques 2 (MCP) et 5 (mémoire) avec le vrai Qwen, copiées dans `preuves/`.
- EVIDENCE.md rempli avec mes vrais résultats.
- Dépôt publié sur GitHub, vérifié par un **clone tout neuf** (tests verts, analyse validée).

## 8. Passage sur le portable et répétition (4 novembre, nuit)

- La soutenance est en présentiel : installation sur mon portable. Une analyse prend 176 s
  (processeur, pas de carte graphique).
- Plan B proposé par moi : ma VM Scaleway. Écarté, parce que le sujet demande que le modèle
  tourne sur mon propre ordinateur.
- Démo réorganisée : lancer l'analyse en premier et présenter pendant qu'elle tourne.
  Répétée en entier. Erreur faite : oublier d'activer `.venv` dans un nouvel onglet.
- Rédaction du journal (`seances.md`) et de ce résumé, puis révision générale par questions.
