# PROGRESS.md : État d'avancement du projet

## 📊 État Global

- **Phase actuelle** : Phase 2 (Implémentation des drivers)
- **Dernier Step validé** : Phase 2.2 (sfr_tv_box_remote.py)

## 📝 Journal des Steps

- [x] **Step 1.1** : base_driver.py (WebSocket Core) - *Priorité Haute*
- [x] **Step 1.2** : discovery.py (mDNS Listener)
- [x] **Step 1.3** : Définir la structure des commandes et créer `sfr_tv_box_core/constants.py` pour les valeurs de commandes partagées.
- [x] **Phase 2.1** : stb8_driver.py - *Priorité Haute*
- [x] **Phase 2.2** : sfr_tv_box_remote.py (Mode "1-shot") - *Priorité Haute*
- [x] **Phase 2.3** : Implémentation du mode d'écoute pour `sfr_tv_box_remote.py` - *Priorité Haute* (Découverte des ports WebSocket: COMMAND sur 7682, NOTIFICATION sur 7684)
- [ ] **Phase 2.4** : stb7_driver.py - *Priorité Moyenne*
- [ ] **Phase 3** : Intégration Home Assistant
- [x] **Phase 4.1** : CI (Workflows GitHub Actions)
- [ ] **Phase 4.2** : CD (Publication)
- [ ] **Phase 4.3** : sfr_tv_box_remote.py (Mode interactif) - *Priorité Moyenne*
- [ ] **Phase 4.4** : Créer le workflow de release (Action GitHub) pour synchroniser la version du `pyproject.toml` vers `manifest.json` lors de la création d'un tag Git. - *Priorité Moyenne*
- [ ] **Phase 5.1** : labox_driver.py - *Priorité Basse*
- [ ] **Phase 5.2** : Implémenter la découverte EVO (Router API via MAC) - *Priorité Basse*
- [ ] **Phase 5.3** : evo_driver.py - *Priorité Basse*

## 🚧 Travail en cours (WIP)

- Analyse APK détaillée pour le messaging WebSocket de la STB8 - Terminée.

## ⏭️ Prochaine Étape (Passage de relais)

- [ ] **Phase 2.3 - Implémentation du mode d'écoute pour `sfr_tv_box_remote.py`**:
    - [x] **Analyse APK détaillée pour le messaging WebSocket de la STB8.**
    - [ ] **Implémenter la génération des commandes STB8**: Basé sur l'analyse de `p361on.C14159a.java` et les structures JSON définies dans `STB8_LISTENER_SPEC.md`, créer ou mettre à jour les fonctions pour générer les messages JSON des commandes "buttonEvent", "getStatus" et "getVersions" pour l'envoi via le WebSocket de commande.
    - [ ] **Implémenter l'envoi des commandes STB8**: S'assurer que les commandes générées sont correctement envoyées via le WebSocket de commande.
    - [ ] **Implémenter le parsing des réponses aux commandes STB8**: Basé sur l'analyse de `p361on.C14160b.java` et de la structure `p297ln.C13163b`, créer les fonctions pour parser les réponses reçues du WebSocket de commande.
    - [ ] **Implémenter le parsing des notifications STB8**: Basé sur l'analyse de `p361on.C14160b.java` et de la structure `p297ln.C13165d`, créer les fonctions pour parser les notifications reçues du WebSocket de notification (notamment l'état "powerOn/Off").
    - [ ] **Intégrer les WebSockets de commande et de notification**: S'assurer que les deux WebSockets sont correctement gérés pour l'envoi de commandes et la réception d'événements.
    - [ ] **Mettre en œuvre la logique de reconnexion automatique**: Avec backoff exponentiel pour les WebSockets.

## 🗂️ Backlog / V2

- [ ] **Amélioration Discovery**: Compléter la `DISCOVERY_SPEC.md` pour récupérer dynamiquement le port, le nom et l'icône de la box.
- [ ] **Analyse `GET_VERSIONS`**: Analyser la structure de la réponse de la commande `GET_VERSIONS`.
- [ ] **Analyse EVO**: Analyser l'architecture des commandes et réponses spécifiques au modèle EVO.
