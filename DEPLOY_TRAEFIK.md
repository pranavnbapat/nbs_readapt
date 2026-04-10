# Traefik Deployment

This deployment is now split into two separate stacks:

- a Traefik proxy stack
- an application stack

That separation is intentional. Traefik should be able to run independently and front multiple applications later.

## Recommended subdomain

Recommended default:

- `nbs-readapt.<your-domain>`

Also reasonable:

- `nbs-repository.<your-domain>`
- `readapt-nbs.<your-domain>`
- `repository.<your-domain>` if this may become part of a larger platform

For now, `nbs-readapt` is a good default.

## Deployment files

### Traefik stack

- [docker-compose.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/docker-compose.yml)
- [traefik.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/traefik.yml)
- [dynamic.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/dynamic.yml)
- [.env](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/.env)
- [.env.sample](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/.env.sample)
- [acme.json](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/acme.json)

### Application stack

- [docker-compose.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/docker-compose.yml)
- [.env](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/.env)

## How the two-stack model works

1. Traefik runs on ports `80` and `443`
2. Traefik creates and uses the shared Docker network `nbs_readapt_proxy`
3. the application stack joins that external proxy network
4. the Django web service exposes Traefik labels, but Traefik itself is not part of the app compose file

## Preparation

### DNS

Point these records to your server:

- `nbs-readapt.<your-domain>`
- optional: `traefik-nbs-readapt.<your-domain>`

### Traefik env

Review and update:

- [deploy/traefik/.env](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/.env)

Key values:

- `APP_DOMAIN`
- `LETSENCRYPT_EMAIL`
- `TRAEFIK_DASHBOARD_HOST`
- `TRAEFIK_DASHBOARD_CREDENTIALS`

Important:

- `LETSENCRYPT_EMAIL` must be a valid real email address
- `TRAEFIK_DASHBOARD_CREDENTIALS` uses `htpasswd` format
- escape `$` as `$$` in the `.env` file

### Root app env

If you use the split deployment layout in `deploy/`, update [deploy/app/.env](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/.env) for production:

- `APP_ENV=production`
- `APP_DEBUG=false`
- `APP_IMAGE=ghcr.io/pranavnbapat/nbs_readapt:latest`
- `APP_DOMAIN=nbs-readapt.<your-domain>`
- `ALLOWED_HOSTS=nbs-readapt.<your-domain>`
- `CSRF_TRUSTED_ORIGINS=https://nbs-readapt.<your-domain>`
- `SECURE_SSL_REDIRECT=true`
- `SESSION_COOKIE_SECURE=true`
- `CSRF_COOKIE_SECURE=true`

Recommended image naming:

- `ghcr.io/pranavnbapat/nbs_readapt:latest`
- or a dated / commit tag such as `ghcr.io/pranavnbapat/nbs_readapt:2026-04-10`

### ACME file permissions

```bash
chmod 600 /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/acme.json
```

This is required. Traefik will skip the ACME resolver if `acme.json` is more open than `600`.

## Launch order

### 1. Start Traefik first

```bash
cd /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik
docker compose up -d
```

This creates the shared proxy network `nbs_readapt_proxy`.

### 2. Start the application stack

```bash
cd /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app
docker compose pull
docker compose up -d
```

## First production checks

After both stacks are up:

```bash
docker logs -f nbs_readapt_traefik
docker compose ps
```

Then:

```bash
curl -kI https://127.0.0.1 -H 'Host: nbs-readapt.<your-domain>'
curl -kI https://127.0.0.1 -H 'Host: traefik-nbs-readapt.<your-domain>'
```

Expected behavior:

- app host returns `200`
- dashboard host returns `401` because of basic auth

If those work, Traefik routing is correct even if public DNS is still propagating.

## DNS requirements

Both public A records must point to the actual server IP:

- `nbs-readapt.<your-domain>`
- `traefik-nbs-readapt.<your-domain>`

If either host points to the wrong server, the symptoms can look misleading:

- hanging `curl` requests
- self-signed or wrong certificates
- requests reaching the wrong machine entirely

Verify with:

```bash
dig +short nbs-readapt.<your-domain>
dig +short traefik-nbs-readapt.<your-domain>
curl -4 ifconfig.me
```

All of those should agree on the same public IPv4 for the intended server.

## Common failure modes

`acme.json` permissions too open

- symptom: Traefik logs say the ACME resolver is skipped
- fix: `chmod 600 acme.json`

Invalid Let's Encrypt contact email

- symptom: logs show `unable to parse email address`
- fix: correct `LETSENCRYPT_EMAIL` and restart Traefik

Wrong DNS A record

- symptom: internal host-header curl works, public domain does not
- fix: point both subdomains to the correct server IP

Private GHCR image

- symptom: `docker compose pull` returns `unauthorized`
- fix: `docker login ghcr.io -u <user>` on the server or make the image public

## Notes

- Traefik is now fully separate from the application compose file
- PostgreSQL and OpenSearch remain internal to the application stack
- the application stack depends on the external `nbs_readapt_proxy` network existing, so Traefik should be started first
- the application stack is now image-based, so the server does not need the full source tree for each deploy
- the application stack now reads deployment settings from `deploy/app/.env`
- this is still a first-pass deployment profile using Django `runserver --insecure` behind Traefik
- the next hardening step would be `gunicorn` plus a stricter static-file strategy
