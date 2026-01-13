# SFR Box Remote (Unified WebSocket Driver)

Pilotage professionnel "Full IP" des décodeurs SFR (V8, V7, LaBox) pour Home Assistant. Ce projet utilise un transport WebSocket bidirectionnel unique, identifié par reverse-engineering de l'APK SFR TV, pour toutes les générations de matériel.

## 1. Architecture du Projet

Le projet est organisé en monorepo pour garantir la cohérence entre la bibliothèque de pilotage et l'intégration domotique.

### A. Librairie Core (`sfr_box_core/`)
Bibliothèque Python 3.12+ autonome (Délivrables 1 & 2).
- **Transport** : Client WebSocket asynchrone unique pour toutes les box.
- **Pattern Strategy (Payloads)** : 
    - `base_driver.py` : Interface de base gérant la session WebSocket et la reconnexion.
    - `v8_driver.py` : Générateur de messages JSON spécifiques à la Box TV 8.
    - `v7_driver.py` : Générateur de messages JSON spécifiques à la Box TV 7.
    - `labox_driver.py` : Générateur de messages pour les versions antérieures.
- **Discovery** : Listener Avahi (`discovery.py`) pour l'identification de la version et l'attribution du bon driver.
- **CLI** : Outil de pilotage en ligne de commande (`cli.py`).

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



You can also make the script directly executable for convenience:

```bash

chmod +x scripts/run_discovery.py

./scripts/run_discovery.py

```



## 3. Structure du Repository



Le projet suit une architecture Monorepo stricte séparant la librairie Core de l'intégration Home Assistant.

Pour le détail complet de l'arborescence et les conventions de développement, veuillez vous référer au fichier [AGENTS.md](./AGENTS.md).
