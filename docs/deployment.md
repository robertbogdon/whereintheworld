# Deployment Guide

## Prerequisites

- Docker and Docker Compose v2
- Python 3 (for secret generation, if not using the container)
- Tailscale (optional, for tailnet exposure)

## Standard Deployment

```bash
# Clone and enter directory
git clone https://github.com/robertbogdon/whereintheworld.git
cd whereintheworld

# Generate secrets
chmod +x generate-secrets.sh
./generate-secrets.sh

# Review configuration
cat .env

# Start services
docker compose up -d

# Verify
curl -s http://localhost:36024/health
```

## Public Hosting

For public deployment (behind a reverse proxy or Tailscale Funnel):

### Security Checklist

1. **Use strong secrets** — `generate-secrets.sh` creates 256-bit random keys
2. **Restrict bind address** — Default `127.0.0.1:36024` ensures the API is not
   exposed on all interfaces. Change to `0.0.0.0` only if intentionally behind
   a reverse proxy.
3. **Use HTTPS** — Tailscale serve provides this automatically. If using a
   public reverse proxy (nginx, Caddy), ensure TLS termination.
4. **Database backups** — The `whereintheworld-pgdata` volume contains all data.
   Back it up regularly.
5. **Monitor logs** — `docker compose logs -f` for operational awareness.

### Environment Overrides

```bash
# Expose on all interfaces for reverse proxy
export HOST_BIND_ADDRESS=0.0.0.0
# Use a non-standard port
export HOST_PORT=8443
```

## Upgrading

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build

# Check logs for migration messages
docker compose logs whereintheworld
```

## Database Maintenance

```bash
# Backup the database volume
docker run --rm -v whereintheworld-pgdata:/source -v $(pwd):/backup \
  alpine tar czf /backup/whereintheworld-backup-$(date +%Y%m%d).tar.gz \
  -C /source .

# Restore
docker run --rm -v whereintheworld-pgdata:/target -v $(pwd):/backup \
  alpine tar xzf /backup/whereintheworld-backup-YYYYMMDD.tar.gz \
  -C /target .
```

## Tailscale Funnel (public internet)

If you want to expose the service to the public internet via Tailscale Funnel:

```bash
# First, serve on tailnet only
tailscale serve --bg --https=36024 localhost:36024

# Then funnel publicly (use with caution!)
tailscale funnel --bg --https=36024 localhost:36024
```

Note: Funnel bypasses the tailnet restriction. Ensure your API key is strong
if you enable Funnel.
