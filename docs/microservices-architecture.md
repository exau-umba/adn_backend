# Architecture microservice ADN PRO SERVICE

## Decoupage par bounded context

Le backend suit les modules metier du front (`adn_webapp/src/modules`) pour conserver une correspondance claire:

- Agents: cycle de vie agent (inscription, competences, statut, disponibilite)
- Users: authentification, comptes internes, gestion des roles RBAC
- Clients: demandes et profil client
- Missions: affectation client-agent
- Contrats: contrats employeur et contrats client
- Finance: paiements, encaissements, historique

## Pattern de communication

- Synchrone HTTP REST pour les interactions front.
- Asynchrone par events RabbitMQ entre services.

Events initiaux:

- `AgentRegistered`
- `AgentStatusChanged`
- `UserRegistered`
- `RoleAssignedToUser`
- `ClientRequestCreated`
- `MissionAssigned`

## Normes de scalabilite

- Identifiants: **UUID** pour les PK metier dans chaque service (voir `docs/services/conventions-identifiers.md`).
- Database per service.
- Health checks (`live`, `ready`) par service.
- Gateway unique pour exposer les APIs.
- Workers asynchrones Celery pour decharger les traitements longs.
- Metrics Prometheus pour autoscaling pilote par observabilite.
