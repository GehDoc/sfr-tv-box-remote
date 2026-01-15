# SFR Box Remote (Unified WebSocket Driver)

Pilotage professionnel "Full IP" des décodeurs SFR (V8, V7, LaBox) pour Home Assistant. Ce projet utilise un transport WebSocket bidirectionnel unique, identifié par reverse-engineering de l'APK SFR TV, pour toutes les générations de matériel.

## 1. Architecture du Projet

Le projet est organisé en monorepo pour garantir la cohérence entre la bibliothèque de pilotage et l'intégration domotique.

### A. Librairie Core (`sfr_box_core/`)

Bibliothèque Python 3.12+ autonome (Délivrables 1 & 2).

- **Transport** : Client WebSocket asynchrone unique pour toutes les box.
- **Stratégie de Commandes (Payloads Polymorphiques)** :
  - `base_driver.py` : Interface de base gérant la session WebSocket, la reconnexion et un système générique pour l'envoi et la réception de commandes (ex: `send_command(command, **params)`). Chaque driver spécialisé implémentera la liste de ses commandes disponibles (`get_available_commands()`).
  - `v8_driver.py` : Définit et implémente les commandes spécifiques à la Box TV 8 (ex: commandes JSON avec paramètres).
  - `v7_driver.py` : Définit et implémente les commandes spécifiques à la Box TV 7.
  - `labox_driver.py` : Définit et implémente les commandes spécifiques à LaBox.
  - `constants.py` : Contient des constantes partagées par la librairie, incluant potentiellement les valeurs de certains paramètres de commande (ex: KeyCodes utilisés par une commande `send_key`).
- **Discovery** : Listener Avahi (`discovery.py`) pour l'identification de la version et l'attribution du bon driver.
- **CLI** : Outil de pilotage en ligne de commande (`sfr_box_remote.py`).

### B. Intégration Home Assistant (`custom_components/sfr_box_remote/`)

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

## 4. Utilities

### Discovery Script

The project includes a command-line utility to discover SFR boxes on your local network. This is useful for testing the discovery mechanism or finding the IP address of your box.

**Location:** `scripts/run_discovery.py`

**Usage:**

To run the script, execute the following command from the root of the project directory:

```bash
python scripts/run_discovery.py
```

The script will scan the network for 10 seconds by default.

**Options:**

*   `-t <seconds>`, `--timeout <seconds>`: Specify the duration of the network scan in seconds.

    *Example (scan for 5 seconds):*
    ```bash
    python scripts/run_discovery.py -t 5
    ```

### SFR Box Remote Control Script

The project includes a command-line utility to send specific commands to an SFR box. This is useful for testing drivers and controlling a box directly from the terminal.

**Location:** `scripts/sfr_box_remote.py`

**Usage:**

To run the script, execute the following command from the root of the project directory:

```bash
PYTHONPATH=. python -m scripts.sfr_box_remote --ip <YOUR_BOX_IP> <COMMAND>
```

**Main Options:**

*   `--ip <IP_ADDRESS>`: **Required.** The IP address of the set-top box.
*   `--port <PORT_NUMBER>`: The port for the WebSocket connection (default: 8080).
*   `--model <MODEL>`: The model of the box (default: STB8). Current supported models: `STB8`.

**Commands:**

*   `SEND_KEY <KEY>`: Send a remote key press.
    *   `<KEY>`: The name of the key to press (e.g., `POWER`, `HOME`, `NUM_5`). Valid keys correspond to the `KeyCode` enum in `sfr_box_core/constants.py`.
    *   *Example:* `PYTHONPATH=. python -m scripts.sfr_box_remote --ip 192.168.1.123 SEND_KEY POWER`

*   `GET_STATUS`: Get the current status of the box.
    *   *Example:* `PYTHONPATH=. python -m scripts.sfr_box_remote --ip 192.168.1.123 GET_STATUS`

*   `GET_VERSIONS`: Get version information from the box.
    *   *Example:* `PYTHONPATH=. python -m scripts.sfr_box_remote --ip 192.168.1.123 GET_VERSIONS`

## 5. Development Setup

To ensure code quality and consistency, this project uses `ruff` for linting and formatting, enforced by `pre-commit` hooks.

### A. Install Development Dependencies

First, ensure you have `pip` installed and then install the development dependencies:

```bash
pip install ".[dev]"
```

### B. Setup Pre-Commit Hooks

Once the development dependencies are installed, set up the pre-commit hooks:

```bash
pre-commit install
```

This command will install the Git hooks that will automatically run `ruff` (linter and formatter) every time you commit changes. This helps catch issues before they become part of the commit history.

## 6. Testing

This project uses `pytest` for unit testing. The tests are located in the `tests/` directory.

To run the tests, ensure you have the necessary dependencies installed (`pytest`, `pytest-asyncio`, `websockets`, `zeroconf`).

**Note:** The `PYTHONPATH=.` prefix is required to ensure that `pytest` can find the `sfr_box_core` module from the project root.

### A. Run All Tests

To run the entire test suite:

```bash
PYTHONPATH=. pytest -v tests/
```

### B. Run a Specific Test File

To run only the tests contained within a single file:

```bash
PYTHONPATH=. pytest -v tests/test_discovery.py
```

### C. Run a Specific Test

To run a single test by its name:

```bash
PYTHONPATH=. pytest -v tests/test_discovery.py::test_discover_single_box_async
```
