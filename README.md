# BookLeaf Author Support Portal

Author and operations portal for BookLeaf Publishing. Authors see only their own books and tickets. Operations staff see the whole queue, override the AI labels, edit a draft, and send the reply. Internal notes stay off the author thread.

## Run it locally

Requirements: Docker Desktop, Python 3.11, Node 20.

From the repo root:

```powershell
docker compose up -d
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.db.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

In a second terminal:

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.

Put a free Groq key in `backend/.env` as `GROQ_API_KEY` before starting the API. Restart the API after any `.env` change. Settings are read once at startup. Gemini is the backup: set `AI_PROVIDER=gemini` and `GEMINI_API_KEY`.

Postgres is published on host port **5433** so it does not collide with a local Postgres on 5432.

## Sign in

Every seeded author uses `Author@123`.

| Who | Email | What to look at |
|---|---|---|
| Priya Sharma | priya.sharma@email.com | Whispers of the Ganges, ₹3,570 pending, a payout already recorded |
| Ananya Reddy | ananya.reddy@email.com | Between Two Temples earned royalty and has never been paid |
| Arjun Malhotra | arjun.malhotra@email.com | Turban Tales, same never-paid case |
| Kavita Deshmukh | kavita.deshmukh@email.com | Raising Roots still in typesetting; The Nagpur Notebooks pending ₹850, under the ₹1,000 line |
| Sneha Kulkarni | sneha.kulkarni@email.com | Midnight in Mysore in cover design; price and royalty stay blank |
| Operations | ops@bookleaf.com | Password `Admin@123`. Queue, draft, notes |

Four sample tickets are seeded: BL-2026-0001 through BL-2026-0004. Later test runs may have added more.

## What the screens do

- Author home, books, ticket list, new query, and read-only thread. The author side uses the sketchbook look.
- Operations queue with status, category, priority, and text filters. Sort is priority, then oldest open ticket. Anything open or in progress for more than 48 hours is marked aging.
- Operations ticket: book facts, editable AI draft, regenerate, send, status and category overrides, assign to me, internal notes. This side uses the ledger look.
- Replies show up without a refresh through a role-scoped event stream. If that stream drops, the page polls every 8 seconds.

## API

All routes are under `/api/v1`. Errors use `{ "error": { "code", "message", "details" } }`.

- `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`
- `GET /books`, `GET /books/{id}`
- `POST /tickets`, `GET /tickets`, `GET /tickets/{id}`
- `GET /admin/stats`, `GET /admin/tickets`, `GET` and `PATCH /admin/tickets/{id}`
- `POST /admin/tickets/{id}/assign`, `/notes`, `/replies`, `/ai/regenerate-draft`
- `GET /events/stream` (bearer token; not a browser EventSource)
- `GET /health`

Authors receive 404 for another author's book or ticket. Notes are always empty on the author ticket payload.

## How the AI works

Creating a ticket saves it first, then classifies and drafts in the background. The request never waits on the model.

1. Keyword rules label category and priority immediately.
2. Groq (`openai/gpt-oss-120b`) may replace that label. The classify prompt does not include the knowledge base.
3. The draft prompt gets only the tone file plus the matching category slice, plus the book numbers from the database.
4. If the key is missing, the model 404s, rate-limits, or times out, the rules stay and the draft is marked failed. Operations can still write the reply.

Royalty answers follow the BookLeaf policy in the knowledge base: 80/20 of net profit, paid quarterly within 45 days of quarter end, and amounts under ₹1,000 roll forward. The model is told not to invent payout dates or ISBN numbers.

Regenerate is a separate call. Drafts are not rewritten on every page view.

## Checks

From `backend`, with the API running:

```powershell
.\.venv\Scripts\python.exe scripts\test_auth.py
.\.venv\Scripts\python.exe scripts\test_tickets.py
.\.venv\Scripts\python.exe scripts\test_ai.py
.\.venv\Scripts\python.exe scripts\test_realtime.py
```

## Free demo hosting

The live pieces are three free accounts, because one free host cannot keep Postgres, a long-running API, and Next.js awake together.

- [Neon](https://neon.tech) for Postgres. The free project sleeps when idle and wakes on the next query. Do not use Render's free database: it is deleted after 30 days.
- [Render](https://render.com) free web service for the API. `render.yaml` in this repo migrates, seeds, and starts Uvicorn. The free instance sleeps after about 15 minutes and takes about a minute to wake. The portal already polls if the live stream drops during that wake.
- [Vercel](https://vercel.com) Hobby for the Next.js app. Set the project root to `frontend` and `NEXT_PUBLIC_API_URL` to the Render URL. Then set the API's `CORS_ORIGINS` to the Vercel URL and redeploy the API.

Paste `GROQ_API_KEY` into the Render service. Render generates `JWT_SECRET`. Neither belongs in git.

## Limits

- Attachment names can be typed with a query. The files are not stored.
- The event stream lives in this API process. A second worker would not see the other worker's events.
- Change `JWT_SECRET` before any shared or public deploy. The example value is only for local use.
- There is no hosted demo URL in this repo. Local Docker Compose is the run path.
