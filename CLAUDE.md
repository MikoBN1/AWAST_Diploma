# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

This is a two-tier monorepo for **AWAST** (Automated Web Application Security Testing):

- `server/` — FastAPI backend (Python 3.10+) that orchestrates scanning, AI exploitation, reporting, and auth.
- `client/awast-front/` — Vue 3 + TypeScript + Vite + Vuetify frontend.
- `server/test_victim/`, `server/xss_strike/`, `server/sqlmap/` — Dockerized helper services (a deliberately vulnerable Flask app for E2E testing, an XSStrike API wrapper, and an sqlmap API wrapper).

The backend is the center of gravity; the frontend is a thin client over its REST + WebSocket API.

## Common Commands

### Full stack (Docker)
```bash
cd server
docker-compose up -d --build      # FastAPI + ZAP + XSStrike + sqlmap + test-victim
```
Service ports: ZAP `8080`, XSStrike `5001→5000`, sqlmap `8775`, test-victim `9999`. The FastAPI server itself runs on `8000` when started with uvicorn (compose does not start it; see below).

### Backend (local dev)
```bash
cd server
python -m venv venv && source venv/bin/activate
pip install -r app/requirements.txt        # NOTE: use app/requirements.txt, not the stub server/requirements.txt
uvicorn app.main:app --reload              # serves on :8000, docs at /docs and /redoc
```
Run only the scanner side-services in Docker: `docker-compose up -d zap xsstrike sqlmap`. When the FastAPI server runs on the host, set `ZAP_API_URL=http://localhost:8080`, `XSSTRIKE_API_URL=http://localhost:5000`, `SQLMAP_API_URL=http://localhost:8775` in `server/app/.env`. When everything runs inside compose, use service-name hosts (`http://zap:8080`, `http://xsstrike:5000`, `http://sqlmap:8775`).

### Frontend
```bash
cd client/awast-front
npm install
npm run dev        # vite dev server, default :5173
npm run build      # vue-tsc type-check + vite build
npm run preview    # serve built bundle
```
`FRONTEND_URL` in backend `.env` must match the dev origin for CORS to allow credentials.

### Tests / scripts
There is no formal test suite. Ad-hoc verification scripts at the `server/` root:
- `python test_alerts.py` — exercises the alerts pipeline.
- `python test_zap.py` — sanity-checks ZAP connectivity.
- `python test_xss_detection.py` — XSS detection check.
Run these only with the relevant docker services up.

## Architecture

### Backend (`server/app/`)
Layered FastAPI app, `main.py` mounts all controllers under `/api/v1`. The lifespan hook calls `core.database.init_models()` which creates tables from SQLAlchemy async models on startup.

- `controllers/` — thin HTTP/WebSocket route handlers (`auth`, `user`, `swagger`, `scanner`, `chain`, `exploiter`, `report`).
- `services/` — business logic. The important ones:
  - `scanner_service.py` — drives OWASP ZAP (spider + active scan), normalizes targets so ZAP-in-Docker can reach `localhost` victims (`localhost:9999` → `test-victim`, others → `host.docker.internal`), dedupes alerts by CWE, and pushes progress over WebSocket.
  - `exploiter_service.py` — the AI exploitation engine. Six techniques (Context-Aware XSS, WAF Bypass, SSTI engine fingerprinting, API parameter guessing for IDOR/Mass Assignment, Prompt Injection, Error-Based SQLi). Generates payloads via `LLMService`, fuzzes with `requests`, validates XSS reflection with `XSSValidator` (an `HTMLParser`) and DOM XSS via `playwright_service.check_dom_xss`. Has fallback static payloads keyed by normalized vuln type.
  - `llm_service.py` — provider-agnostic LLM client; provider is selected by `LLM_PROVIDER` env (`gemini` | `groq` | `claude`).
  - `chain_service.py` — composes individual findings into attack chains using `SEVERITY_SCORE` and `VULN_TYPE_MAP` to normalize ZAP's verbose alert names into canonical types.
  - `websocket_service.py` (`manager`) — connection registry used by scanner and exploiter to stream categorized events (`info`/`log`/`attack`/`success`/`failed`) keyed by a client-supplied `ws_id`.
  - `report_service.py` — ReportLab-based PDF generation.
  - `database_service.py`, `user_service.py`, `ai_checker_service.py`, `swagger_service.py`, `playwright_service.py` — supporting services.
- `plugins/` — per-vuln detection helpers (`xss_reflected`, `sqli_basic`, `ssrf_oob`, `idor_enum`, plus `common_helpers`). These are reusable detection primitives, not the AI exploitation logic.
- `models/` — SQLAlchemy async models: `User`, `Scan`, `Vulnerability`. `Base` is declared in `core/database.py`; models must be imported inside `init_models()` to avoid circular imports (this pattern is intentional — don't move them to module-level imports in `database.py`).
- `schemas/` — Pydantic request/response schemas.
- `core/` — `config.py` (pydantic-settings, loads `app/.env`), `database.py` (async engine + session), `security.py` (auth/jwt).

### Vuln-type normalization
ZAP emits many string variants for the same class (e.g. `"Cross Site Scripting (Reflected)"`, `"SQL Injection - MySQL"`). Two separate maps exist:
- `ExploiterService.VULN_TYPE_ALIASES` in `exploiter_service.py` — collapses to short keys like `"XSS"`, `"SQL Injection"`.
- `VULN_TYPE_MAP` in `chain_service.py` — collapses to similar but **not identical** keys (`"SQLi"` vs `"SQL Injection"`).
When adding a new ZAP alert string, update **both** maps; they serve different downstream consumers.

### Exploiter request/WebSocket contract
`POST /api/v1/exploiter/run` body: `{ target, params, vuln_type, cookies, method, ws_id }`. The client opens `WS /api/v1/exploiter/ws/{ws_id}` *before* posting, then receives streamed events of types `info | log | attack | success | failed` until the HTTP call resolves with `status: "confirmed" | "potential"`. Session auth is passed as raw `cookies` in the body — there is no browser-login step. See `server/EXPLOITER_README.md` for full details.

### Target normalization quirk
`scanner_service._normalize_target_for_zap` rewrites `localhost`/`127.0.0.1`/`::1` URLs so a Dockerized ZAP can reach the host. Port `9999` is special-cased to `test-victim` (the bundled vulnerable app on the same compose network); other ports map to `host.docker.internal`. Keep this in mind when debugging "ZAP can't reach target" issues — the URL the user submits is *not* the URL ZAP sees.

### Frontend (`client/awast-front/src/`)
Vue 3 SFCs with Pinia for state, vue-router for routing, vue-i18n for localization, Vuetify + MDI/Bootstrap icons for UI, axios for HTTP, vue-chartjs for charts. Standard layout: `views/`, `components/`, `stores/`, `services/` (axios clients), `router/`, `i18n/`, `types/`. Build is type-checked (`vue-tsc -b`) before bundling.

## Configuration

Backend env file is `server/app/.env` (loaded by `core/config.py`, **not** `server/.env`). Required and notable keys:
- `DATABASE_URL` (required) — async SQLAlchemy URL (e.g. `sqlite+aiosqlite:///./session.db`).
- `FRONTEND_URL` — exact origin for CORS (default `http://localhost:5173`).
- `ZAP_API_KEY`, `ZAP_API_URL`, `ZAP_MIN_CONFIDENCE` (`Low|Medium|High`, controls false-positive filtering).
- `XSSTRIKE_API_URL`, `SQLMAP_API_URL`.
- `LLM_PROVIDER` (`gemini|groq|claude`) plus the matching `*_API_KEY` and `*_MODEL` for the chosen provider.

## Documentation pointers

- `server/README.md` — full setup, endpoint catalogue, mermaid architecture diagram.
- `server/EXPLOITER_README.md` — exploitation engine internals and WS event contract.
- `server/docs/WEBSOCKET_API.md` — WebSocket message schema for scan progress.
- `server/docs/EMPIRICAL_DATA_ANALYSIS.md`, `server/docs/PRESENTATION_6_SLIDES.md` — diploma writeup material.
