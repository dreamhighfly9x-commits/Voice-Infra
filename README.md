# Voice-Infra

Deploy `Voice-Backend` (FastAPI + VieNeu-TTS) and `Voice-Frontend` (built
static app served by nginx, reverse-proxying `/api` to the backend) with
Docker Compose.

## Run

```bash
docker compose up --build
```

First boot downloads the VieNeu-TTS model from Hugging Face into the
`voice_storage` volume's process — actually into the container's pip cache
inside the image layer / HF cache, not the volume; expect the backend
healthcheck to stay "starting" for a few minutes on the very first run
(`start_period: 300s` gives it room). Then open **http://localhost**.

`voice_storage` (mounted at `/data` in the backend container) holds
generated `audio/*.wav` files and `recordings.json` — back this up / mount
it on persistent storage in production.

## Logs

All containers log to stdout. Docker's `json-file` driver rotates the logs at 10 MB × 5 files per container (the `x-logging` block in `docker-compose.yml`).

- The backend, api, worker, and nginx write one JSON object per line.
- nginx passes an `X-Request-ID` to the backend, so nginx and backend lines for one request share a `request_id`.
- Set `LOG_LEVEL` (default `info`) and `APP_VERSION` in the host env.

```bash
docker compose logs -f api
docker compose logs --no-log-prefix backend | jq 'select(.level=="error")'
docker compose logs --no-log-prefix backend frontend | jq 'select(.request_id=="<id>")'
```

## GPU

The default image is CPU-only (VieNeu-TTS ships torch-free by default). For
CUDA inference, extend `Dockerfile.backend` to install the `cuda` extra
(`pip install vieneu[cuda]` plus a CUDA-enabled base image) — see
`Voice-Backend/README.md` and the upstream repo's GPU install instructions.

## What's missing for a real production deploy

This compose file is dev/staging-shaped: no TLS termination, no
Postgres/Redis, no auth. `docs/02-ky-thuat/build-plan-tts.md` in the workspace root
describes the fuller design (accounts, RBAC, job queue, GPU worker pool)
this can grow into once the product needs multi-user accounts and quotas
rather than a single shared recordings list.
