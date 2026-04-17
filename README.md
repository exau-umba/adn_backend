# ADN Backend - Architecture Microservices

Base microservice backend pour ADN PRO SERVICE, alignee sur les modules du webapp.

## Services metier cibles

- `agents_service` (implante)
- `users_service` (authentification + roles RBAC)
- `clients_service` (a venir)
- `missions_service` (a venir)
- `contrats_service` (a venir)
- `finance_service` (a venir)

## Technologies microservices

- Django + DRF (API metier)
- JWT (SimpleJWT) pour auth stateless
- PostgreSQL (base par service)
- RabbitMQ (events inter-services)
- Redis + Celery (asynchrone et traitement de fond)
- Nginx (API Gateway)
- Prometheus + Grafana (monitoring)

## Documentation des services

- `docs/services/conventions-identifiers.md` (UUID pour toutes les PK metier)
- `docs/services/users-service.md`
- `docs/services/agents-service.md`
- `docs/services/service-documentation-template.md` (modele pour les prochains services)

## JWT (access token)

- Duree par defaut: **15 minutes** (`JWT_ACCESS_LIFETIME_MINUTES` dans les `.env` des services `users` et `agents`).
- Apres expiration, le client doit appeler `POST /api/users/auth/refresh/` avec le refresh token, ou se reconnecter.

## Persistance des bases PostgreSQL (Docker)

Les donnees sont stockees dans des **volumes nommes** (`agents_db_data`, `users_db_data`).

- `docker compose -f infra/docker-compose.yml up --build` : **conserve** les volumes ; un rebuild d’image ne supprime pas les donnees.
- `docker compose down` (sans `-v`) : **conserve** les volumes.
- `docker compose down -v` ou `docker volume rm ...` : **efface** les donnees. A n’utiliser que si tu veux repartir de zero.

Pour sauvegarder avant un nettoyage: export SQL (`pg_dump`) ou copie du volume.

## Lancement local

```bash
cd adn_backend
docker compose -f infra/docker-compose.yml up --build
```

Endpoints via gateway:

- `http://localhost:8080/api/agents/`
- `http://localhost:8080/api/users/auth/register/`
- `http://localhost:8080/api/users/auth/login/`
- `http://localhost:8080/api/users/auth/me/`
- `http://localhost:8080/health/live`
- `http://localhost:8080/health/users/live`
