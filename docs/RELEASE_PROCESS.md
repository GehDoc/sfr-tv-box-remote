# Processus de Release (SFR TV Box Remote)

Ce document détaille le processus de versioning et de release pour le projet SFR TV Box Remote, basé sur un workflow Git Flow simplifié (GitHub Flow) et l'utilisation de GitHub Actions.

## 1. Stratégie de Versioning

### A. Source Unique de Vérité (pyproject.toml)

La version du projet est définie dans le fichier `pyproject.toml` à la racine du dépôt. C'est la seule source officielle de la version du projet.

* **Exemple :**

    ```toml
    [project]
    name = "sfr-tv-box-remote"
    version = "0.1.0"
    ```

### B. Synchronisation de la Version pour HACS

Pour le composant Home Assistant (HACS), la version doit être présente dans `custom_components/sfr_tv_box_remote/manifest.json`. Un workflow GitHub Actions sera responsable de synchroniser cette version depuis `pyproject.toml` vers `manifest.json` lors du processus de release.

## 2. Processus de Release

Le projet suit un workflow GitHub Flow simplifié avec une seule branche principale (`main`).

### A. Développement

1. **Branches de Fonctionnalités :** Tout le développement de nouvelles fonctionnalités ou la correction de bugs se fait sur des branches de fonctionnalités dédiées, créées à partir de `main` (ex: `feat/nouvelle-fonctionnalite`, `fix/bug-correction`).
2. **Pull Requests (PR) :** Le code est intégré dans la branche `main` uniquement via des Pull Requests (PRs). Chaque PR doit être revue, approuvée et passer la CI avant d'être fusionnée.

### B. Préparation de la Release

1. **Décision de Release :** Une release est décidée lorsqu'un ensemble de fonctionnalités est jugé stable et prêt pour la publication.
2. **Incrementation de Version :** La version du projet est **manuellement incrémentée** dans `pyproject.toml` (ex: de `0.1.0` à `0.1.1` pour un patch, `0.2.0` pour une fonctionnalité). Cette modification doit faire partie d'un commit dédié à la release.
    * **Convention sémantique :** Il est recommandé de suivre le Versioning Sémantique (SemVer - `MAJEUR.MINEUR.PATCH`).
3. **Commit de Release :** Le changement de version dans `pyproject.toml` est inclus dans un commit avec un message explicite (ex: `chore: Release v0.1.1`). Ce commit est fusionné dans `main` via une PR ou directement si la protection de branche n'est pas encore active.

### C. Déclenchement de la Release (GitHub Actions)

1. **Création du Tag Git :** Une fois le commit de release fusionné dans `main`, un **tag Git est créé** sur ce commit en respectant la convention `vX.Y.Z` (ex: `git tag v0.1.1`).
2. **Workflow CI/CD :** La création de ce tag Git `vX.Y.Z` déclenchera un workflow GitHub Actions (`.github/workflows/release.yml`) qui exécutera les étapes suivantes :
    * **Validation :** Exécuter la suite de tests et les outils de linting.
    * **Mise à jour du `manifest.json` HACS :** Lire la version depuis `pyproject.toml` et la mettre à jour dans `custom_components/sfr_tv_box_remote/manifest.json`.
    * **Création de la Release GitHub :** Générer une Release GitHub officielle, potentiellement avec un changelog automatique (si configuré) et l'ajout d'artefacts de release.
    * (Future : Déclencher la publication vers PyPI, Docker, ou d'autres plateformes si applicable, ainsi que la notification à HACS.)

## 3. Gestion des Dépendances

La gestion des dépendances Python est centralisée dans `pyproject.toml`.

## 4. Maintenance

* **Corrections de Bugs :** Les corrections de bugs sont traitées comme des fonctionnalités et passent par le même cycle (branche -> PR -> `main`).
* **Mises à Jour :** Les mises à jour mineures et majeures suivent le même processus.
