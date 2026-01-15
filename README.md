# SFR TV Box Remote (Unified WebSocket Driver)

Pilotage professionnel "Full IP" des décodeurs SFR (V8, V7, LaBox) pour Home Assistant. Ce projet utilise un transport WebSocket bidirectionnel unique, identifié par reverse-engineering de l'APK SFR TV, pour toutes les générations de matériel.

## 1. Architecture du Projet

Le projet est organisé en monorepo pour garantir la cohérence entre la bibliothèque de pilotage et l'intégration domotique.

### A. Librairie Core (`sfr_tv_box_core/`)

Bibliothèque Python 3.12+ autonome (Délivrables 1 & 2).

- **Transport** : Client WebSocket asynchrone unique pour toutes les box.
- **Stratégie de Commandes (Payloads Polymorphiques)** :
  - `base_driver.py` : Interface de base gérant la session WebSocket, la reconnexion et un système générique pour l'envoi et la réception de commandes (ex: `send_command(command, **params)`). Chaque driver spécialisé implémentera la liste de ses commandes disponibles (`get_available_commands()`).
  - `stb8_driver.py` : Définit et implémente les commandes spécifiques à la Box TV 8 (ex: commandes JSON avec paramètres).
  - `stb7_driver.py` : Définit et implémente les commandes spécifiques à la Box TV 7.
  - `labox_driver.py` : Définit et implémente les commandes spécifiques à LaBox.
  - `constants.py` : Contient des constantes partagées par la librairie, incluant potentiellement les valeurs de certains paramètres de commande (ex: KeyCodes utilisés par une commande `send_key`).
- **Discovery** : Listener Avahi (`discovery.py`) pour l'identification de la version et l'attribution du bon driver.
- **CLI** : Outil de pilotage en ligne de commande (`sfr_tv_box_remote.py`).

### B. Intégration Home Assistant (`custom_components/sfr_tv_box_remote/`)

Composant personnalisé prêt pour HACS (Délivrables 3 & 5).

- **Mode** : `local_push`. Le WebSocket permet une remontée d'état instantanée (changement de chaîne, volume, power) vers HA sans interrogation (polling).
- **Entités** : `media_player.py` et `remote.py`.

### C. Ressources et Qualité

- **`ui/`** : Templates YAML pour l'interface Lovelace (Délivrable 4).
- **`tests/`** : Suite de tests unitaires et mocks WebSocket (Pytest).
- **`.github/`** : Workflows pour la Continuous Integration (CI).

## 2. Spécifications Techniques

- **Source de Vérité** : Protocoles et KeyCodes extraits du code Kotlin/Java de l'APK SFR TV.
- **Langage** : Python 3.12 (Asynchrone via `asyncio`).
- **Robustesse** : Gestion de la reconnexion avec backoff exponentiel et monitoring de la connexion (Heartbeat).

## 3. Structure du Repository

Le projet suit une architecture Monorepo stricte séparant la librairie Core de l'intégration Home Assistant.

Pour le détail complet de l'arborescence et les conventions de développement, veuillez vous référer au fichier [AGENTS.md](./AGENTS.md).

## 4. Utilitaires

### Script de Découverte

Ce projet inclut un utilitaire en ligne de commande pour découvrir les box SFR sur votre réseau local. Il est utile pour tester le mécanisme de découverte ou trouver l'adresse IP de votre box.

**Emplacement :** `scripts/run_discovery.py`

**Utilisation :**

Pour exécuter le script, lancez la commande suivante depuis la racine du répertoire du projet :

```bash
python scripts/run_discovery.py
```

Le script recherchera les box pendant 10 secondes par défaut.

**Options :**

*   `-t <secondes>`, `--timeout <secondes>` : Spécifie la durée (en secondes) de la recherche réseau.

    *Exemple (recherche pendant 5 secondes) :*
    ```bash
    python scripts/run_discovery.py -t 5
    ```

### Script de Contrôle à Distance SFR TV Box

Ce projet inclut un utilitaire en ligne de commande pour envoyer des commandes spécifiques à une box SFR. Il est utile pour tester les drivers et contrôler une box directement depuis le terminal.

**Emplacement :** `scripts/sfr_tv_box_remote.py`

**Utilisation :**

Pour exécuter le script, lancez la commande suivante depuis la racine du répertoire du projet :

```bash
PYTHONPATH=. python scripts/sfr_tv_box_remote.py --ip <ADRESSE_IP_DE_VOTRE_BOX> <COMMANDE>
```

**Options Principales :**

*   `--ip <ADRESSE_IP>` : **Requis.** L'adresse IP de la box.
*   `--port <NUMERO_DE_PORT>` : Le port pour la connexion WebSocket (par défaut : 8080).
*   `--model <MODELE>` : Le modèle de la box (par défaut : STB8). Modèles supportés actuellement : `STB8`.

**Commandes :**

*   `SEND_KEY <TOUCHE>` : Envoie une pression de touche de télécommande.
    *   `<TOUCHE>` : Le nom de la touche à presser (par exemple, `POWER`, `HOME`, `NUM_5`). Les touches valides correspondent aux membres de l'énumération `KeyCode` dans `sfr_tv_box_core/constants.py`.
    *   *Exemple :* `PYTHONPATH=. python scripts/sfr_tv_box_remote.py --ip 192.168.1.133 SEND_KEY POWER`

*   `GET_STATUS` : Obtient le statut actuel de la box.
    *   *Exemple :* `PYTHONPATH=. python scripts/sfr_tv_box_remote.py --ip 192.168.1.133 GET_STATUS`

*   `GET_VERSIONS` : Obtient les informations de version de la box.
    *   *Exemple :* `PYTHONPATH=. python scripts/sfr_tv_box_remote.py --ip 192.168.1.133 GET_VERSIONS`

## 5. Documentation du Projet

Pour une analyse approfondie des spécifications du projet, de l'état d'avancement du développement et des structures de commandes détaillées, veuillez vous référer aux documents suivants :

*   **[Spécifications et Roadmap du Projet](PROJECT_SPEC.md)** : Définit l'architecture globale, le backlog fonctionnel et les standards de développement.
*   **[Avancement du Projet et Prochaines Étapes](PROGRESS.md)** : Suit le statut actuel, les tâches terminées et les phases de développement à venir.
*   **[Documentation Technique (docs/)](docs/)** : Contient les spécifications détaillées pour les commandes, les mécanismes de découverte et d'autres aspects techniques.

    *   [Spécification des Commandes et Payloads](docs/COMMANDS_SPEC.md)
    *   [Spécification du Protocole de Découverte](docs/DISCOVERY_SPEC.md)

## 6. Configuration de Développement

Pour garantir la qualité et la cohérence du code, ce projet utilise `ruff` pour le linting et le formatage, appliqués par des hooks `pre-commit`.

### A. Installation des Dépendances de Développement

Tout d'abord, assurez-vous que `pip` est installé, puis installez les dépendances de développement :

```bash
pip install ".[dev]"
```

### B. Configuration des Hooks Pre-Commit

Une fois les dépendances de développement installées, configurez les hooks `pre-commit` :

```bash
pre-commit install
```

Cette commande installera les hooks Git qui exécuteront automatiquement `ruff` (linter et formateur) à chaque fois que vous ferez un commit. Cela permet de détecter les problèmes avant qu'ils ne fassent partie de l'historique des commits.

## 7. Tests

Ce projet utilise `pytest` pour les tests unitaires. Les tests sont situés dans le répertoire `tests/`.

Pour exécuter les tests, assurez-vous d'avoir installé les dépendances nécessaires (`pytest`, `pytest-asyncio`, `websockets`, `zeroconf`).

**Note :** Le préfixe `PYTHONPATH=.` est nécessaire pour que `pytest` puisse trouver le module `sfr_tv_box_core` depuis la racine du projet.

### A. Exécuter tous les tests

Pour exécuter la suite de tests complète :

```bash
PYTHONPATH=. pytest -v tests/
```

### B. Exécuter un fichier de test spécifique

Pour exécuter uniquement les tests contenus dans un seul fichier :

```bash
PYTHONPATH=. pytest -v tests/test_discovery.py
```

### C. Exécuter un test spécifique

Pour exécuter un seul test par son nom :

```bash
PYTHONPATH=. pytest -v tests/test_discovery.py::test_discover_single_box_async
```
