# RAISC Backend

**We're building RAISC in public** — a mental health platform that connects people seeking support with psychologists, clinics, and AI-assisted intake.

This repository is the **Django API** that powers RAISC. It started as a student project and is being shaped into a real product by a small team iterating openly. Expect active development, imperfect edges, and frequent improvements.

- Product: [raisc.org](https://raisc.org/)
- Staging: [stage.raisc.org](https://stage.raisc.org/)

> **Branch note:** The latest feature work lives on [`stage-demo`](https://github.com/hammad-ahmed-01/RAISC_backend/tree/stage-demo). That's the branch this README describes.

---

## What we're building

RAISC is designed around a hybrid care model:

1. **Start with conversation** — patients can begin with guided AI chat; session insights sync into their clinical profile.
2. **Connect with a psychologist** — discover doctors, send requests, schedule and reschedule sessions, share summaries.
3. **Track how you're doing** — simple mood check-ins over time.
4. **Find peer support** — anonymous group Q&A with real-time chat, where clinicians can also respond.
5. **Support clinics** — organization accounts manage doctor rosters and clinic calendars.

We're not claiming to replace therapy. We're building tools that make mental health support more reachable — for individuals and for the clinics that serve them.

---

## Status

This is **early public infrastructure**, not a finished product.

| Area | State |
|------|--------|
| Auth & roles (patient, doctor, organization, staff) | Working |
| Therapy sessions & reschedule requests | Working |
| Mood tracking | Working |
| Peer support chat (REST + WebSockets) | Working |
| Organization / clinic management | Working |
| In-app notifications + email (AWS SES) | Working on `stage-demo` |
| AI chatbot ↔ Django profile sync | Working (external bot posts summaries) |
| Standalone FastAPI chat stub | Dev / experimental |
| Production hardening | In progress |

Feedback, issues, and thoughtful PRs are welcome. Please treat mental-health-related contributions with care and respect.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| API | Django 5 + Django REST Framework |
| Real-time | Django Channels + Redis + Daphne |
| Database | PostgreSQL |
| Auth | Token authentication (DRF) |
| Email | AWS SES (optional) |
| Deploy | Gunicorn, Docker, Nixpacks-friendly |
| Dev AI stub | FastAPI (`fast_api_chat/`) |

Typical companion app: a Next.js frontend talking to this API over REST and WebSockets.

---

## Architecture (high level)

```
Frontend (Next.js)
    │  REST + WebSocket
    ▼
Django + DRF + Channels
    ├── users / patients / doctors
    ├── chat              (peer support)
    ├── organization      (clinics)
    ├── notifications     (in-app + email)
    ├── PostgreSQL
    └── Redis

AI chat service  ──POST session summaries──►  /users/patient/data/<token>/
```

---

## Apps in this repo

| App | Role |
|-----|------|
| `users` | Auth, custom user model, shared calendar/sessions |
| `patients` | Patient profiles, mood, dashboard, chatbot data sync |
| `doctors` | Discovery, patient requests, sessions, ratings, reschedule flow |
| `chat` | Support groups, threaded Q&A, WebSocket consumers |
| `organization` | Clinic profiles, affiliated doctors, org calendars |
| `notifications` | In-app notifications and email alerts |
| `fast_api_chat` | Lightweight standalone chatbot for local experiments |

---

## Getting started

### Prerequisites

- Python **3.11+**
- PostgreSQL
- Redis (required for Channels / real-time chat)

### 1. Clone

```bash
git clone https://github.com/hammad-ahmed-01/RAISC_backend.git
cd RAISC_backend
git checkout stage-demo
```

### 2. Virtual environment & dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> On `stage-demo`, email features also need `boto3`. Image uploads may need `Pillow`. Install them if you hit import errors:
>
> ```bash
> pip install boto3 Pillow
> ```

### 3. Environment

Create a `.env` in the project root (already gitignored):

```bash
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
POSTGRES_DB=RAISC_DB
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional — email notifications (AWS SES)
EMAIL_ENABLED=false
AWS_SES_REGION=ap-southeast-2
SENDER_EMAIL=notifications@your-verified-domain.com
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

### 4. Database & Redis

Create the PostgreSQL database, start Redis, then:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run

```bash
# HTTP API (development)
python manage.py runserver

# For WebSockets / Channels in production-like setups, use Daphne or your ASGI stack
```

API defaults to `http://127.0.0.1:8000/`.

Optional local FastAPI stub:

```bash
cd fast_api_chat
uvicorn main:app --reload --port 8001
```

---

## API map (overview)

Trailing slashes are **disabled** (`APPEND_SLASH = False`).

| Area | Base | Examples |
|------|------|----------|
| Auth & profile | `/users/` | `register/`, `login/`, `user/`, `profile/` |
| Patient | `/users/patient/` | `dashboard/`, `mood-today/`, `set-mood/`, `sessions/` |
| Doctor | `/users/doctor/` | `list/`, `request/<id>/`, `sessions/`, `reschedule-requests/` |
| Chat (REST) | `/chat/` | `groups/`, questions & answers under a group |
| Chat (WS) | `ws/chat/<group_id>/` | Real-time group thread |
| Organization | `/organization/` | org list/details, doctors, register doctor |
| Notifications | `/api/notifications/` | list, unread count, mark read |
| AI bridge | `/users/patient/data/<token>/` | Chatbot → profile / summary sync |

Explore exact routes in each app's `urls.py`, or via Django admin / your API client.

---

## Docker

A basic production-style image is included:

```bash
docker build -t raisc-backend .
docker run --env-file .env -p 8000:8000 raisc-backend
```

The container runs Gunicorn against `RAISC_backend.wsgi`. For WebSockets, prefer an ASGI server (e.g. Daphne) in front of Channels.

---

## Building in public

We're a small team shipping this openly so others can follow along, learn from the journey, and help where it makes sense.

**Ways to contribute**

- Open an issue for bugs or product ideas
- Discuss before large PRs
- Prefer focused changes that match existing style
- Never commit secrets, patient data, or real clinical notes

**Please keep in mind**

- This is mental health software — design and communicate with empathy
- Do not use this repo to store or share real personal health information in issues or PRs
- Security reports are appreciated; avoid publishing exploit details publicly until we've had a chance to fix them

---

## Team

Built by contributors including **Hammad Ahmed**, **Usman Javaid**, **Yusra**, and others who have pushed this from an FYP into a living product. Names and roles will evolve as we grow.

---

## License

Licensing for public use is still being finalized. Until then, assume **all rights reserved** — feel free to explore and open issues; ask before redistributing or building a competing commercial fork from this code.

---

## Disclaimer

RAISC is a technology platform under active development. It is **not** a crisis service, medical device, or substitute for professional care. If you or someone you know is in immediate danger, contact local emergency services or a trusted crisis line.
