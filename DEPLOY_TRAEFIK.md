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

- [docker-compose.traefik.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/docker-compose.traefik.yml)
- [traefik.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/traefik.yml)
- [dynamic.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/dynamic.yml)
- [.env](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/.env)
- [.env.sample](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/.env.sample)
- [acme.json](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/acme.json)

### Application stack

- [docker-compose.app.yml](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/docker-compose.app.yml)
- [.env.sample](/home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/.env.sample)

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

### App env

Copy:

```bash
cp /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/.env.sample /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app/.env
```

Update:

- `APP_DOMAIN`

### Root app env

Update the root [.env](/home/pranav/PyCharm/Parveen/nbs_readapt/.env) for production:

- `APP_ENV=production`
- `APP_DEBUG=false`
- `ALLOWED_HOSTS=nbs-readapt.<your-domain>`
- `CSRF_TRUSTED_ORIGINS=https://nbs-readapt.<your-domain>`
- `SECURE_SSL_REDIRECT=true`
- `SESSION_COOKIE_SECURE=true`
- `CSRF_COOKIE_SECURE=true`

### ACME file permissions

```bash
chmod 600 /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik/acme.json
```

## Launch order

### 1. Start Traefik first

```bash
cd /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/traefik
docker compose -f docker-compose.traefik.yml up -d
```

This creates the shared proxy network `nbs_readapt_proxy`.

### 2. Start the application stack

```bash
cd /home/pranav/PyCharm/Parveen/nbs_readapt/deploy/app
docker compose -f docker-compose.app.yml up --build -d
```

## Notes

- Traefik is now fully separate from the application compose file
- PostgreSQL and OpenSearch remain internal to the application stack
- the application stack depends on the external `nbs_readapt_proxy` network existing, so Traefik should be started first
- this is still a first-pass deployment profile using Django `runserver --insecure` behind Traefik
- the next hardening step would be `gunicorn` plus a stricter static-file strategy
