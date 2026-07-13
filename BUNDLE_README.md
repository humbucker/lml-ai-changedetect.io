# LML Venue Change Detection — Setup Guide

This bundle contains a self-contained instance of the LML venue change detection system — 250 venue websites monitored for changes, with a JSON API for querying results.

## Requirements

- **Docker Desktop** installed — download from https://www.docker.com/products/docker-desktop/
- Ports **5000** and **8080** free on your machine

## Setup (5 minutes)

**Step 1 — Unzip the bundle**

Unzip `lml-change-detection-bundle.zip` into a folder. Open a terminal and navigate to that folder.

**Step 2 — Import the venue data**

```bash
docker volume create changedetection_changedetection-data
docker run --rm \
  -v changedetection_changedetection-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/changedetection-data.tar.gz -C /data
```

**Step 3 — Start the stack**

```bash
docker compose up -d
```

Wait about 30 seconds for everything to start, then check http://localhost:5000 loads in your browser.

**Step 4 — Get the API key and connect the venue-status service**

- Open http://localhost:5000
- Go to **Settings → API**
- Copy the API key
- Open `compose.yaml` in a text editor
- Replace the `CHANGEDETECTION_API_KEY` value with your key
- Save the file, then run:

```bash
docker compose restart venue-status-api
```

That's it.

---

## What's running

| Service | URL | Description |
|---|---|---|
| changedetection.io | http://localhost:5000 | Web UI — browse all venues, view diffs, adjust settings |
| Venue Status API | http://localhost:8080/venue-change-status | JSON API — one entry per venue |

---

## Using the API

**All 250 venues:**
```
http://localhost:8080/venue-change-status
```

**Venues that changed since a date:**
```
http://localhost:8080/venue-change-status?changed_since=2026-07-01
```

**Single venue by LML UUID:**
```
http://localhost:8080/venue-change-status?lml_uuid=1a51e558-1f5b-4329-9dc7-79fcb55dccad
```

**Health check:**
```
http://localhost:8080/health
```

See `docs/venue-change-status-api.md` for full API documentation.

---

## What's included

- **250 venues** across Geelong, Fitzroy, St Kilda, Queenscliff, Goldfields, and Surf Coast
- All sourced from LML Admin Central — venues with public websites only (Facebook/Instagram-only venues excluded)
- Pre-configured to check every **Monday at 8am**
- Playwright (headless Chrome) included for sites that require JavaScript rendering

---

## Stopping and starting

```bash
docker compose stop      # stop without losing data
docker compose start     # start again
docker compose down      # stop and remove containers (data is preserved in the volume)
```

---

## Exposing publicly

To make the API accessible from outside your machine, set up a Cloudflare Tunnel or nginx reverse proxy pointing at port 8080. See https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ for a free option.

---

## Support

Contact Nick Thorpe — nicko@unfold-labs.com
