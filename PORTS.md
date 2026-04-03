# Port Allocation Policy

All host-facing ports for this project must stay in the `9500-9599` range.

This is a deliberate project convention for local development and handover clarity.

## Current live assignments

- `9500`: Django web application
- `9501`: PostgreSQL host access
- `9502`: pgAdmin
- `9503`: OpenSearch API
- `9504`: OpenSearch metrics

Reserved:

- `9505`: MySQL if ever introduced later
- `9506`: phpMyAdmin if ever introduced later

## Service mapping

`web`

- container port: `8000`
- host port: `9500`

`postgres`

- container port: `5432`
- host port: `9501`

`pgadmin`

- container port: `80`
- host port: `9502`

`opensearch`

- API container port: `9200`
- API host port: `9503`
- metrics container port: `9600`
- metrics host port: `9504`

## Rule

If a new host-facing service is added:

1. assign a port within `9500-9599`
2. update this file
3. keep the same value in:
   - `docker-compose.yml`
   - `.env`
   - `.env.sample`
   - any related markdown documentation

## Examples

Correct:

- application on `9510`
- Redis on `9511`
- Nginx on `9512`

Incorrect:

- exposing a project service on `8000`
- exposing a project service on `5432`
- using a random untracked host port
