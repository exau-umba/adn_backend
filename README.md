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

- `docs/services/users-service.md`
- `docs/services/agents-service.md`
- `docs/services/service-documentation-template.md` (modele pour les prochains services)

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
