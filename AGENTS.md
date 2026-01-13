# Protocole et Contexte du Projet SFR-Box-Remote

Ce document définit les règles d'interaction, l'architecture technique et la méthodologie de développement pour tout agent IA travaillant sur ce dépôt.

## 1. Vision et Socle Technique

Le projet consiste à développer un pilote professionnel pour les décodeurs SFR (V8, V7, LaBox) pour Home Assistant.

* **Transport** : Protocole **WebSocket unique** pour toutes les versions (unification confirmée).
* **Source de Vérité** : Code Kotlin/Java issu du reverse-engineering de l'APK SFR TV.
* **Langage** : Python 3.12+ (Asynchronisme via `asyncio`).
* **Architecture** : Monorepo séparant la librairie Core et l'intégration Home Assistant.

## 2. Structure du Repository

```text
sfr-box-remote/
├── .github/              # Workflows CI/CD (GitHub Actions)
├── scripts/              # Répertoire de tooling
│   └── init_project.sh   # Votre script d'initialisation
├── docs/                 # Documentation technique approfondie
├── AGENTS.md             # Contrat d'interaction (Ce fichier)
├── PROJECT_SPEC.md       # Roadmap et spécifications fonctionnelles
├── PROGRESS.md           # Journal de suivi et état d'avancement (Passage de relais)
├── README.md             # Présentation et guide utilisateur
├── pyproject.toml        # Dépendances (websockets, zeroconf, aiohttp)
├── sfr_box_core/         # DÉLIVRABLE : Librairie Python autonome
│   ├── __init__.py
│   ├── base_driver.py    # Classe ABC : Gestion commune du WebSocket
│   ├── v8_driver.py      # Payloads JSON spécifiques à la Box 8
│   ├── v7_driver.py      # Payloads JSON spécifiques à la Box 7
│   ├── labox_driver.py   # Payloads JSON spécifiques à LaBox
│   ├── discovery.py      # Listener Avahi/mDNS (Détection auto)
│   └── constants.py      # KeyCodes et Endpoints issus de l'APK
├── custom_components/    # DÉLIVRABLE : Intégration Home Assistant
│   └── sfr_box_remote/   # Manifest, media_player.py, remote.py
├── ui/                   # DÉLIVRABLE : Templates Lovelace (YAML)
└── tests/                # Suite de tests Pytest (Mocks WebSocket)

```

## 3. Méthodologie d'Interaction (Obligatoire)

Tout agent doit opérer selon le cycle suivant :

1. **Spécification (SPEC)** : Pour toute nouvelle fonctionnalité, un document `[NOM_FONCTIONNALITÉ]_SPEC.md` en majuscules doit être créé dans `/docs`. Ce document doit être validé par l'utilisateur avant de commencer l'implémentation.
2. **Approche Atomique** : Ne traiter qu'un seul fichier ou une seule brique logique par réponse.
3. **Test-Driven Development (TDD)** : Chaque fonctionnalité doit être livrée avec son test unitaire (dans `/tests`) simulant les réponses de la box.
4. **Qualité du Code (Linting & Formatting)** : Appliquer les outils de qualité de code (linter, formateur) définis dans le projet (`ruff`).
5. **Documentation** : Mettre à jour la documentation pertinente (ex: `README.md`, docstrings, etc.).
6. **Validation & Itération** : L'agent doit attendre la validation de l'utilisateur (et la publication Git) avant de passer à l'étape suivante.

## 4. Instructions de Programmation

* **Gestion Réseau** : Implémenter obligatoirement une reconnexion automatique avec backoff exponentiel dans `base_driver.py`.
* **Logging** : Chaque interaction WebSocket doit être tracée via le module `logging`.
* **Modularité** : La librairie `sfr_box_core` ne doit avoir aucune dépendance vers les bibliothèques internes de Home Assistant.

## 5. Continuité et Passage de Relais (Stockage d'État)

Afin qu'un agent puisse passer le relais à un autre, un fichier **`PROGRESS.md`** doit être maintenu à jour à chaque fin de session ou étape majeure. Ce fichier doit contenir :

1. **État Actuel** : Quel est le dernier fichier validé et testé.
2. **Encours (WIP)** : Quelles sont les tâches entamées mais non terminées.
3. **Blocages** : Problèmes rencontrés ou informations manquantes (ex: KeyCode APK non encore traduit).
4. **Next Step** : La tâche précise par laquelle le prochain agent doit commencer.

**Instruction pour l'agent arrivant** : Lire `AGENTS.md` puis `PROGRESS.md` pour synchroniser son contexte avant toute proposition.
