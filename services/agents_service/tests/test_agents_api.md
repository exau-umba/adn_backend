# Scenarios de test API agents

1. Creer un agent avec competences et disponibilites.
2. Lister les agents avec filtre status=ACTIVE.
3. Suspendre un agent via /api/agents/{id}/suspend/.
4. Reactiver un agent via /api/agents/{id}/reactivate/.
5. Verifier les logs worker Celery pour les events.
