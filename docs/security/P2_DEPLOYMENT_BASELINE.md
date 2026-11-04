# P2 secure development/deployment baseline

Tracks #35 and #36 under epic #16.

## Current posture
- The base Compose file is **local development only**. Web/API listen on
  127.0.0.1 and PostgreSQL, Redis and MinIO have no host-published ports.
  They are still accessible to trusted containers on the Compose network.
- The API fails startup in `INVESTHELPER_ENV=production` unless it receives
  a PostgreSQL connection and a nontrivial password.
- PostgreSQL and MinIO secrets must be supplied explicitly via an untracked
  `.env` or environment injection. Do not reuse the sample placeholders.
- These controls do NOT constitute complete production security. Authentication,
  authorization, network policies, TLS between managed services, monitoring,
  backups, and external security review remain mandatory before public launch.

## Private local setup

```sh
cp .env.example .env
# Set long unique passwords in .env. Never add .env to git.
docker compose config --quiet
docker compose up --build
```

The only host URLs are http://127.0.0.1:3000 and http://127.0.0.1:8000.
Do not port-forward them to the public internet.

## Production recommendations
- Use a managed PostgreSQL with private networking, backups and TLS.
- Deploy behind a TLS-terminating proxy and authenticated entry point.
- Inject secrets through the hosting provider, not client-side NEXT_PUBLIC variables.
- Don't deploy this base Compose YAML as a public production stack.
- Deploy the P2 auth and authorization work (#37) before storing user portfolios
  or watchlists or enabling public write access.
- A GitHub merge does not publish a service or set hosting secrets.

## Verification
`python scripts/check_compose_security.py` enforces private DB/Redis/MinIO
ports and mandatory credential interpolation. Tests reject weak production
credentials and cover the Compose policy.
