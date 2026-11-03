# EVIDENCE — Copilote de recon nmap vérifié

Modèle : **Qwen3.5-4B Q4_K_M** via Ollama, en local (RTX 3050 6 Go), contexte 8192 tokens.
Une section par brique : ce que je montre, les fichiers, la commande qui le reproduit.

> Les parties marquées **[À REMPLIR]** se complètent avec les vraies sorties de Qwen
> sur ma machine : je copie la trace dans `preuves/` et je colle l'extrait ici.

---

## Brique 1 — Mon propre outil

**Ce que je montre.** `lire_scan(chemin)` lit un fichier XML nmap et ne garde que les
ports à l'état exact `open` (pas `closed`, `filtered`, ni `open|filtered`).
`lancer_scan(cible)` lance nmap avec des options fixes puis appelle `lire_scan`.
Le modèle les appelle dans la boucle que j'ai écrite (`agent.py`). La trace contient
l'appel (nom, arguments) et le résultat.

**Fichiers.** `copilote/outils_nmap.py`, `copilote/agent.py` (fonction `analyser`),
`tests/test_outils_nmap.py` (les 10 scans du benchmark + cas limites).

**Reproduire.**
```bash
python -m copilote "Analyse le scan donnees/scans_bench/scan_01.xml"
python -m pytest tests/test_outils_nmap.py -v
```

**Trace d'un vrai appel.** [À REMPLIR] : `preuves/brique1_appel_outil.json`
(extrait : `{"outil": "lire_scan", "arguments": {...}, "resultat": {...}}`)

---

## Brique 2 — Mon propre serveur MCP

**Ce que je montre.** `serveur_mcp.py` expose `lire_scan` et `lancer_scan` en MCP (stdio).
`harness_mcp.py` est un harness : il démarre le serveur, lui demande la liste de ses outils,
la donne à Qwen, et chaque appel d'outil de Qwen passe par le protocole MCP.
Les garde-fous restent actifs côté serveur.

**Fichiers.** `copilote/serveur_mcp.py`, `copilote/harness_mcp.py`, `tests/test_mcp_et_bench.py`.

**Reproduire.**
```bash
python -m copilote.harness_mcp --sans-llm        # appel MCP direct, sans modèle
python -m copilote.harness_mcp "Analyse le scan donnees/scans_bench/scan_09.xml"
python -m pytest tests/test_mcp_et_bench.py -v   # démarre le vrai serveur
```

**Trace d'un vrai appel.** [À REMPLIR] : `preuves/brique2_mcp.json`

---

## Brique 3 — Des règles imposées par le code

**Ce que je montre.** Trois choses que le système ne doit jamais faire, empêchées par du
Python et non par le prompt :

| Règle | Où | Test qui essaie de l'enfreindre |
|---|---|---|
| Scanner hors périmètre (Internet, réseau d'un autre, injection `127.0.0.1; rm -rf /`) | `verifier_cible()` appelé au début de `lancer_scan()` | `test_cibles_interdites`, `test_lancer_scan_hors_perimetre_ne_lance_jamais_nmap`, `test_le_modele_demande_une_cible_interdite` |
| Lire un fichier hors `donnees/` (`../../etc/passwd`) | `verifier_chemin()` dans `lire_scan()` | `test_chemins_interdits`, `test_le_modele_essaie_de_lire_un_fichier_systeme` |
| Montrer une réponse qui cite un port non ouvert | `verifier_reponse()` dans `analyser()` | `test_port_invente_dans_le_texte`, `test_hallucination_deux_fois_reponse_rejetee` |

Le test `test_lancer_scan_hors_perimetre_ne_lance_jamais_nmap` remplace `subprocess.run`
par une fonction qui fait échouer le test : il prouve que nmap n'est **jamais** lancé.

**Fichiers.** `copilote/garde_fous.py`, `tests/test_garde_fous.py`, `tests/test_agent.py`.

**Reproduire.**
```bash
python -m pytest tests/test_garde_fous.py tests/test_agent.py -v
python -m copilote "Scanne 8.8.8.8"
```

**Avec le vrai modèle.** [À REMPLIR] : sortie de `python -m copilote "Scanne 8.8.8.8"`
(ligne `[GARDE-FOU] lancer_scan({'cible': '8.8.8.8'}) -> REFUSÉ ...`).

**Bug trouvé pendant le développement.** Une ligne `Ports: 22, 80 et port 9999` en haut
de la réponse était prise pour la ligne finale et ignorée : le port inventé 9999 passait.
Corrigé dans `ports_cites()` (seule la dernière ligne `PORTS:` est retirée), avec le test
`test_port_cache_dans_une_autre_ligne_ports`.

---

## Brique 5 — Mémoire entre les sessions

**Ce que je montre.** Après chaque analyse **validée**, `memoire.json` garde la cible, la
date et les ports ouverts. À la session suivante (nouveau processus), quand le même hôte
est analysé, le souvenir est ajouté au résultat de l'outil : le modèle peut dire quels
ports sont apparus ou ont disparu. Une réponse rejetée n'est jamais mémorisée.

**Coût en tokens.** Le souvenir fait environ 30 à 40 tokens par cible (estimation
4 caractères/token, champ `memoire_estimee` de la trace). [À REMPLIR] : `prompt_tokens`
mesurés par Ollama, session 1 vs session 2.

**Fichiers.** `copilote/memoire.py`, `tests/test_memoire.py`.

**Reproduire (test après redémarrage).**
```bash
python -m pytest tests/test_memoire.py -v
# avec le modèle : deux processus séparés
python -m copilote "Analyse le scan donnees/scans_bench/scan_05.xml"
python -m copilote "Analyse le scan donnees/scans_bench/scan_05.xml"   # se souvient
```

---

## Brique 9 — Comparaison mesurée

**Protocole.**
- Deux séries de 10 tâches à réponse connue, générées par `donnees/generer_scans.py`
  (la vérité est écrite par ce script, pas par `lire_scan`) :
  - **facile** (`scan_01` à `scan_10`, `bench/taches.json`) : 2 à 20 ports ouverts, quelques
    pièges (`closed`, `filtered`, `open|filtered`, SSH sur 2222) ;
  - **difficile** (`scan_11` à `scan_20`, `bench/taches_difficiles.json`) : 30 à 46 ports ouverts,
    25 leurres TCP, et des numéros présents à la fois en TCP `closed` et en UDP `open` ou
    `open|filtered`.
- **Qwen seul** : le XML brut est collé dans le prompt, la réponse est prise telle quelle.
- **Mon système** : Qwen + outil + vérification + une correction.
- Même modèle, contexte 8192, température 0.7, **3 lancements** chacun, moyenne ± écart-type.
- Une réponse est « juste » si sa ligne `PORTS:` donne exactement les ports ouverts.
  Mesure principale : le taux de réponses **fausses montrées à l'utilisateur**.

**Reproduire.**
```bash
python bench/comparer.py                      # série facile
python bench/comparer.py --serie difficile    # série difficile
python bench/echecs.py resultats/bench_<serie>_XXXX.json
```

### Résultat 1 — série facile (3 novembre 2026, `resultats/bench_20261103_162008.json`)

| Mesure | Qwen seul | Mon système |
|---|---|---|
| Réponses justes (taux) | 1.00 ± 0.00 | 1.00 ± 0.00 |
| Réponses FAUSSES montrées (taux) | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Réponses rejetées (taux) | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Ports inventés (total par lancement) | 0.00 ± 0.00 | 0.00 ± 0.00 |

**Lecture : effet plafond.** Sur ces 10 scans, Qwen seul ne se trompe jamais : le benchmark
est trop facile pour séparer les deux systèmes, et ne permet pas de conclure que mon système
apporte quelque chose. Je garde ce résultat tel quel et j'ai construit la série difficile
pour tester là où un petit modèle a des chances de se tromper (beaucoup de ports, contexte
long, pièges TCP/UDP).

### Résultat 2 — série difficile

[À REMPLIR : coller le tableau affiché par `python bench/comparer.py --serie difficile`]

| Mesure | Qwen seul | Mon système |
|---|---|---|
| Réponses justes (taux) | | |
| Réponses FAUSSES montrées (taux) | | |
| Réponses rejetées (taux) | | |
| Ports inventés (total par lancement) | | |

**Un échec expliqué à partir de sa trace.** [À REMPLIR avec `bench/echecs.py`] :
quelle tâche, quel lancement, ce que le modèle a répondu, pourquoi c'est faux
(port `closed` compté comme ouvert ? port oublié dans une longue liste ? confusion TCP/UDP ?
prompt tronqué : regarder `tokens.prompt` par rapport à 8192), et ce que mon système a fait.

**Ce que ces chiffres ne permettent pas de conclure.** Avec 10 tâches par série et
3 lancements, l'écart-type est grossier. Les scans sont synthétiques (format nmap réel,
contenu construit) : rien ne garantit les mêmes taux sur de vrais réseaux. J'ai ajouté la
série difficile **après** avoir vu le résultat de la série facile : les deux résultats sont
rapportés, mais la série difficile a été conçue pour être dure. On mesure la fidélité des
ports, pas la qualité des conseils : sur un vrai scan de ma machine, Qwen a cité des ports
justes mais un conseil hors sujet (« évasion de conteneurs » pour SMB), que mon vérificateur
ne détecte pas.
