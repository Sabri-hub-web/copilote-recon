# EVIDENCE — Copilote de recon nmap vérifié

Modèle : **Qwen3.5-4B Q4_K_M** via Ollama, en local (RTX 3050 6 Go), contexte 8192 tokens.
Une section par brique : ce que je montre, les fichiers, la commande qui le reproduit.

> Toutes les preuves ci-dessous viennent de lancements réels de Qwen3.5-4B sur ma machine,
> le 3 novembre 2026. Les traces retenues sont copiées dans `preuves/`.

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

**Trace d'un vrai appel.** `preuves/brique1_scan_reel_localhost.json` : Qwen a appelé
`lancer_scan({"cible": "127.0.0.1"})`, nmap a réellement scanné ma machine, et l'outil a renvoyé
les ports ouverts 135/tcp (msrpc) et 445/tcp (microsoft-ds). Réponse finale vérifiée :
`PORTS: 135,445`.

Commande : `python -m copilote "Scanne 127.0.0.1 et dis-moi par où commencer"`.

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

**Trace d'un vrai appel (Qwen3.5-4B, 3 novembre 2026).** `preuves/brique2_mcp.json`.
Le harness affiche `Outils exposés par le serveur MCP : ['lire_scan', 'lancer_scan']`, puis Qwen
appelle `lire_scan({"chemin": "donnees/scans_bench/scan_09.xml"})` via MCP. Le serveur renvoie
les 4 ports ouverts (2222, 8443, 9200, 27017) et la réponse est validée :
`PORTS: 2222, 8443, 9200, 27017`. Qwen n'a pas cité le port 22, présent dans le scan mais
`closed` (SSH tourne ici sur 2222).

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

**Avec le vrai modèle (Qwen3.5-4B, 3 novembre 2026).**
```
[GARDE-FOU] lancer_scan({'cible': '8.8.8.8'}) -> REFUSÉ par le garde-fou : 8.8.8.8 est hors du périmètre autorisé
```
Après le refus, Qwen a essayé **de lui-même** une autre cible, `127.0.0.1` (autorisée). Un agent
autonome peut donc changer de cible sans demander : c'est pour cela que le périmètre est imposé
par le code et pas par le prompt. Dans la même session, Qwen a aussi inventé le port 3389 sur
`scan_12` pendant le benchmark ; `verifier_reponse` l'a refusé (voir brique 9).

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

**Test après redémarrage avec le vrai modèle (3 novembre 2026).** Deux processus séparés,
même scan (`scan_05`, cible 172.17.0.6) :

| | Session 1 (cible inconnue) | Session 2 (après redémarrage) |
|---|---|---|
| Souvenir ajouté au résultat de l'outil | non | oui : ports [21, 22, 80] et date |
| `memoire_estimee` (estimation 4 car./token) | 0 | 32 |
| `prompt_tokens` mesurés par Ollama | 1 368 | 1 437 (+69) |

Traces : `preuves/brique5_session1.json` et `preuves/brique5_session2.json`.

**Ce que cela coûte, et ce que cela n'a pas fait.** Le souvenir coûte environ 70 tokens de
prompt par cible connue (mon estimation à 4 caractères/token le sous-estime : 32 contre ≈ 69
mesurés ; l'écart vient aussi de la variation naturelle des tours). Dans cette session 2, Qwen a
reçu le souvenir mais ne l'a pas mentionné dans sa réponse (rien n'avait changé) : la mémoire
est bien gardée et transmise, mais son usage par le modèle n'est pas garanti.

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

### Résultat 2 — série difficile (3 novembre 2026, `resultats/bench_difficile_20261103_180617.json`)

| Mesure | Qwen seul | Mon système |
|---|---|---|
| Réponses justes (taux) | 0.00 ± 0.00 | 1.00 ± 0.00 |
| Réponses FAUSSES montrées (taux) | 1.00 ± 0.00 | 0.00 ± 0.00 |
| Réponses rejetées (taux) | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Ports inventés (total par lancement) | 0.00 ± 0.00 | 0.00 ± 0.00 |

Mesures complémentaires, calculées à partir des traces du même fichier (30 réponses chacun) :

| | Qwen seul | Mon système |
|---|---|---|
| Réponses sans ligne `PORTS:` | 29 / 30 | 0 / 30 |
| Réponses complètement vides | 28 / 30 | 0 / 30 |
| Ports oubliés en moyenne | 37,2 | 0,0 |
| Tokens du prompt (moyenne) | 4 178 | 3 193 (cumul sur tous les tours) |
| Prompt + tokens générés | 8 188 en moyenne, 8 192 au maximum | — |
| Réponses de Qwen corrigées par le vérificateur | — | 6 / 30 |

**Échec expliqué n° 1 — Qwen seul, lancement 1, `scan_11` (43 ports ouverts).**
La trace contient une réponse **vide** : 0 port annoncé, donc 43 ports oubliés. Les compteurs de
tokens expliquent pourquoi : le XML brut collé dans le prompt coûte à lui seul ≈ 4 200 tokens.
Qwen raisonne ensuite (bloc de réflexion) pendant ≈ 4 000 tokens, et prompt + génération
atteignent 8 188 tokens en moyenne, 8 192 au maximum : **la fenêtre de contexte de 8 192 tokens
est pleine avant que le modèle n'écrive sa réponse**. Ce n'est donc pas une hallucination mais un
épuisement du budget de contexte, sur 28 réponses sur 30.
Mon système évite ce mur parce que l'outil `lire_scan` ne renvoie au modèle qu'un JSON compact
des ports ouverts, au lieu du XML complet avec les 25 leurres et les balises.

**Échec expliqué n° 2 — mon système, lancement 1, `scan_12` : une hallucination attrapée.**
Première réponse de Qwen refusée par `verifier_reponse` :
`port 3389 cité dans le texte mais il n'est pas ouvert dans le scan`. Le port 3389 (RDP, le bureau
à distance de Windows) n'apparaît **nulle part** dans `scan_12`, ni ouvert ni comme leurre :
le modèle l'a inventé, probablement parce que c'est un port « attendu » dans ce genre d'analyse.
Le message d'erreur a été renvoyé à Qwen, sa seconde réponse était juste, et c'est celle-là qui a
été montrée. Les 5 autres corrections (`scan_17`, `scan_13`, `scan_16`, `scan_19`, `scan_20`)
concernent une ligne `PORTS:` absente de la première réponse.

**Ce que ces chiffres ne permettent pas de conclure.** Avec 10 tâches par série et
3 lancements, l'écart-type est grossier. Les scans sont synthétiques (format nmap réel,
contenu construit) : rien ne garantit les mêmes taux sur de vrais réseaux. J'ai ajouté la
série difficile **après** avoir vu le résultat de la série facile : les deux résultats sont
rapportés, mais la série difficile a été conçue pour être dure. L'écart sur la série difficile
vient surtout de la limite de contexte (8 192 tokens, imposée par le sujet) : avec une fenêtre
plus grande, ou en désactivant la réflexion de Qwen, Qwen seul ferait probablement mieux, et je
ne l'ai pas mesuré. Ce que montre la série difficile, c'est que donner au modèle un résultat
d'outil compact plutôt que les données brutes évite de saturer le contexte. On mesure la fidélité des
ports, pas la qualité des conseils : sur un vrai scan de ma machine, Qwen a cité des ports
justes mais un conseil hors sujet (« évasion de conteneurs » pour SMB), que mon vérificateur
ne détecte pas.
