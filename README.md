# Deep Research Podcaster — Python Backend

## Folder structure

```
podcast-backend/
├── app/
│   ├── main.py          # FastAPI app entrypoint — creates `app`, wires CORS, health check
│   ├── api/              # Route handlers only (Phase 2+). Each file = one feature's endpoints.
│   │                      #   Thin layer: parses request, calls a service, returns response.
│   │                      #   No business logic and no direct external API calls live here.
│   ├── services/          # Business logic + external API calls (Gemini, Fish Audio, mixing).
│   │                      #   This is the Python equivalent of your old geminiService.ts,
│   │                      #   except it runs on the server, so API keys never leave it.
│   ├── models/            # Pydantic models: request/response schemas for the API,
│   │                      #   plus any internal data classes (e.g. a DialogueLine).
│   ├── core/               # Cross-cutting concerns used by everything else:
│   │                      #   config.py (env vars), logging_config.py, exceptions.py.
│   └── utils/              # Small, stateless helper functions with no business logic
│                            #   of their own (string cleanup, filename sanitizing, etc.)
├── audio_output/           # Generated MP3/WAV files land here at runtime. Git-ignored
│                            #   except for a .gitkeep placeholder, so the folder exists
│                            #   on a fresh clone even before anything's been generated.
├── tests/                  # pytest test files, mirroring the app/ structure.
├── requirements.txt        # Exact pinned dependency versions.
├── .env.example             # Template for the real .env file (never commit real .env).
└── README.md
```

## Why this structure specifically

- **`api/` vs `services/` split**: this is the single most important structural decision in
  the whole backend, and it directly fixes the biggest architectural flaw in your original
  project. In the JS version, `App.tsx` (the "route handler" equivalent) called Fish Audio's
  API *directly*. Here, route handlers in `api/` are never allowed to call `httpx` or any
  external API themselves — they only call functions in `services/`. This isn't just tidiness:
  it means every external call goes through one tested, retried, logged code path, and it
  means you can unit-test `services/` functions without spinning up the whole web server.
- **`core/config.py` as the only place reading env vars**: prevents the exact bug class where
  `fishApiKey` was silently `undefined` in your original code because the env var name didn't
  match — Pydantic validates required fields exist at startup and crashes immediately with a
  clear error if not, instead of failing deep inside a fetch call three phases later.

## Running Phase 1

```bash
cd podcast-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env and paste your real API keys
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/health — you should see:

```json
{"status": "ok", "environment": "development"}
```

And http://127.0.0.1:8000/docs gives you FastAPI's auto-generated interactive API
documentation — this is your built-in Postman replacement, and it's the tool you'll use
to test each new endpoint as we build it in the coming phases.

## What "done" looks like for Phase 1

- [ ] `pip install -r requirements.txt` succeeds with no errors
- [ ] `.env` exists locally with your real keys (and is NOT committed to git)
- [ ] `uvicorn app.main:app --reload` starts without crashing
- [ ] `/health` returns `{"status": "ok", ...}`
- [ ] `/docs` loads in the browser

If `uvicorn` fails to start with a Pydantic validation error, that's expected and good —
it means a required env var is missing from `.env`. Read the error message; it names the
exact field, which is the whole point of validating config at startup instead of at runtime.
