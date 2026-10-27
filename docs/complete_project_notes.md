# 📚 NEURO Learning Platform — Complete Project Notes
> **For Project Evaluation | Prepared: May 2026**  
> *A Django-based web application for children with special needs — 4-member group project*

---

## 🎯 1. Project Overview

**NEURO** (NeuroLearn) is a comprehensive **learning and therapy web platform** designed specifically for children with special needs (e.g., autism spectrum, developmental delays). It provides personalized, role-aware experiences for everyone involved in a child's care.

### Core Purpose
- Give children a safe, interactive space to learn letters, numbers, words, emotions, and play skill-building games.
- Give teachers and therapists tools to manage routines, monitor progress, and communicate with parents.
- Give parents real-time visibility into their child's activities and receive push notification reminders.

### Access URL
```
http://127.0.0.1:8000        → Main App
http://127.0.0.1:8000/admin  → Django Admin Panel
```

---

## 👥 2. User Roles & Dashboards

The platform has **4 distinct user roles**, each with a dedicated dashboard:

| Role | Dashboard Route | Key Features |
|------|----------------|--------------|
| **Child** | `/dashboard/` → `dashboard_child.html` | Learning modules, games, drawing canvas, AAC board |
| **Teacher** | `/dashboard/` → `dashboard_teacher.html` | Student management, routines, analytics, video calls |
| **Parent** | `/dashboard/` → `dashboard_parent.html` | Child progress overview, push notifications, messaging |
| **Therapist** | `/dashboard/` → `dashboard_teacher.html` | Same as teacher — routine/activity management |

> The system uses Django's session-based auth. After login, the view reads `request.user.role` and renders the appropriate dashboard template.

### Test Accounts (pre-seeded)
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@neurolearn.com | NeuroLearn2024! |
| Teacher | teacher@neurolearn.com | Teacher123! |
| Parent | parent@neurolearn.com | Parent123! |
| Child | child@neurolearn.com | Child123! |
| Therapist | therapist@neurolearn.com | Therapist123! |

---

## 🏗️ 3. Project Structure

```
Neuro_WebApp-main/
├── neurolearn/              ← Django project config (settings, URLs, ASGI/WSGI)
│   ├── settings.py          ← All configuration (DB, apps, Redis, Celery, CORS)
│   ├── urls.py              ← Root URL dispatcher
│   ├── asgi.py              ← ASGI + Django Channels WebSocket setup
│   ├── wsgi.py              ← Traditional WSGI entry point
│   └── celery.py            ← Celery app initialization
│
├── apps/                    ← All Django application modules
│   ├── users/               ← Auth, profiles, dashboards, analytics
│   ├── learning/            ← Alphabet, Numbers, Words, Emotions modules
│   ├── routines/            ← Visual schedules, timetables, notifications
│   ├── games/               ← Color matching, animal matching games
│   ├── drawing/             ← Canvas drawing tool
│   ├── messaging/           ← Real-time WebSocket messaging + WebRTC video calls
│   └── communication/       ← AAC (Augmentative & Alternative Communication) board
│
├── templates/               ← All Django HTML templates
├── static/                  ← CSS, JS, images, audio
│   └── js/
│       ├── webrtc_call.js           ← Full WebRTC video call implementation
│       ├── drawing_canvas.js        ← HTML5 Canvas drawing tool
│       ├── learning_iframe_bridge.js← Bridges Django ↔ React learning apps
│       ├── aac_shared.js            ← AAC keyboard/speech synthesis
│       ├── fcm_registration.js      ← Firebase Cloud Messaging token registration
│       ├── letter_tracing.js        ← Letter tracing interaction
│       ├── number_counting.js       ← Number counting interaction
│       └── word_matching.js         ← Word matching interaction
│
├── media/                   ← User-uploaded files (profile pics, drawings, etc.)
├── db.sqlite3               ← SQLite database (development)
├── manage.py                ← Django management entry point
└── requirements.txt         ← Python dependencies
```

---

## 🔧 4. Tech Stack — Complete with Where Each Is Used

### 4.1 Backend

#### **Django 5.2.4** ← *Core Framework*
- **Used in**: Every Python file across all apps (`models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`)
- Handles: HTTP routing, ORM (database queries), template rendering, form validation, sessions, admin UI
- Config file: `neurolearn/settings.py`

#### **Django REST Framework (DRF) 3.16.0** ← *REST API Layer*
- **Used in**: `apps/users/api_views.py`, `apps/learning/serializers.py`, `apps/routines/serializers.py`
- Provides JSON API endpoints for the React-based learning apps (alphabet, numbers, words) that communicate via `learning_iframe_bridge.js`
- Setting: `REST_FRAMEWORK` block in `settings.py`

#### **Django Channels 4.x + Daphne** ← *WebSocket / Real-time*
- **Used in**: `neurolearn/asgi.py`, `apps/messaging/consumers.py`, `apps/messaging/routing.py`
- Enables WebSocket connections for:
  - **Video call signaling** (WebRTC SDP/ICE exchange)
  - **Real-time messaging** between users
- `consumers.py` → `VideoCallConsumer` handles the full call lifecycle (connect, signal relay, disconnect)
- `asgi.py` routes HTTP to Django and WebSocket to Channels

#### **channels_redis 4.x** ← *Channel Layer Backend*
- **Used in**: `neurolearn/settings.py` → `CHANNEL_LAYERS`
- Acts as message broker between WebSocket consumers (multiple Django workers share state via Redis)
- Connection: `redis://127.0.0.1:6379`

#### **Celery 5.4.0** ← *Background Task Queue*
- **Used in**: `neurolearn/celery.py`, `apps/routines/tasks.py`
- Runs the scheduled task `check_and_send_routine_notifications` **every minute** (via Celery Beat)
- Task checks which child routines are due right now and triggers Firebase push notifications to parents/children

#### **Redis 5.0.x** ← *Broker for Celery + Channel Layer*
- **Used as**: Message broker for Celery task queue AND as Django Channels channel layer backend
- Connection: port `6379` on localhost
- Required to be running before starting the Django server in real-time mode

#### **Pillow 11.3.0** ← *Image Processing*
- **Used in**: Any model with `ImageField` (profile pictures, task images, letter/number/word images, animal images)
- Handles image upload, storage and serving via Django's media file system

#### **python-decouple 3.8** ← *Environment Variable Management*
- **Used in**: `neurolearn/settings.py` (wraps `config()` calls)
- Reads `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CELERY_BROKER_URL` from a `.env` file (or falls back to defaults for development)

#### **django-cors-headers 4.3.1** ← *CORS Policy*
- **Used in**: `neurolearn/settings.py` → `CORS_ALLOWED_ORIGINS`, middleware stack
- Allows the React learning module iframes (running on same origin) to make fetch requests to the Django API
- Middleware: `corsheaders.middleware.CorsMiddleware` (must be first in middleware list)

#### **firebase-admin 6.5.0** ← *Push Notifications*
- **Used in**: `apps/routines/notifications.py`
- Sends **Firebase Cloud Messaging (FCM)** push notifications to parent and child devices
- Triggered by the Celery scheduled task when a routine's time matches the current time
- Requires `serviceAccountKey.json` from Firebase Console

---

### 4.2 Database

#### **SQLite** ← *Development Database*
- **Location**: `db.sqlite3` in project root
- Used during development — no setup required
- Configured in `settings.py` → `DATABASES`

#### **PostgreSQL** ← *Production-Ready (not active in dev)*
- Mentioned in README as the production target
- Django ORM is database-agnostic — switching requires only `settings.py` change

---

### 4.3 Frontend

#### **HTML5 + Django Template Language (DTL)**
- **Used in**: All files in `templates/` directory
- Django templates use `{% %}` tags for logic and `{{ }}` for variables
- `templates/base.html` → master layout (navbar, footer, scripts)
- Each app has its own subfolder: `templates/users/`, `templates/learning/`, etc.

#### **CSS3 (Vanilla CSS + Custom Tokens)**
- **Used in**: `static/css/` directory
- Color design tokens are documented in `colour tokens.md`
- No CSS framework like Tailwind — custom styling throughout

#### **Bootstrap 5** ← *UI Component Framework*
- **Used in**: Loaded via CDN in `templates/base.html`
- Grid layout, cards, modals, buttons, forms, navbar across all dashboards
- Badge, spinner, progress bar components

#### **JavaScript (Vanilla ES6+)**
All JS files are in `static/js/`:

| File | Purpose | Key APIs Used |
|------|---------|---------------|
| `webrtc_call.js` | Full video call implementation | WebRTC (`RTCPeerConnection`), WebSocket |
| `drawing_canvas.js` | Free-draw canvas tool | HTML5 Canvas 2D API |
| `learning_iframe_bridge.js` | Parent page ↔ iframe messaging | `postMessage` / `onmessage` |
| `aac_shared.js` | AAC board speech output | Web Speech API (`speechSynthesis`) |
| `fcm_registration.js` | Register device for push notifications | Firebase JS SDK, `navigator.serviceWorker` |
| `letter_tracing.js` | Letter tracing in learning module | Canvas / touch/mouse events |
| `number_counting.js` | Number counting interaction | DOM manipulation |
| `word_matching.js` | Word-image matching game logic | DOM events |

#### **WebRTC** ← *Peer-to-Peer Video Calling*
- **Used in**: `static/js/webrtc_call.js`
- Full call flow: `call-request → incoming popup → accept → SDP offer/answer → ICE candidates → live video`
- STUN servers (Google): `stun.l.google.com:19302` for NAT traversal
- Signaling done over Django Channels WebSocket (`ws://host/ws/call/<user_id>/`)
- Supports: mic mute, camera toggle, auto-reject when busy, 45-second timeout, ringtone audio

#### **Firebase JavaScript SDK** ← *Client-side FCM*
- **Used in**: `static/js/fcm_registration.js`
- Registers the browser/device with Firebase and stores the FCM token in the backend (via `ParentDevice` model)
- Pairs with `firebase-admin` on the server side for sending notifications

#### **Material Icons**
- **Used in**: `templates/base.html` and across templates
- Loaded via Google Fonts CDN
- Used extensively in the AAC board (`communication` app), nav icons, action buttons

---

### 4.4 Real-Time Architecture

```
Browser A (Teacher)                    Browser B (Parent/Child)
     |                                       |
  WebSocket                             WebSocket
     |                                       |
     └──────── Django Channels ─────────────┘
                    |
              Redis Channel Layer
                    |
           VideoCallConsumer
           (apps/messaging/consumers.py)
```

**WebRTC Call Flow:**
1. Teacher clicks "Video Call" → `initSignaling()` opens WebSocket to `/ws/call/<child_id>/`
2. Sends `call-request` signal → Django relays to child's browser
3. Child sees incoming call modal → clicks Accept → sends `call-accepted`
4. Teacher creates `RTCPeerConnection`, gets camera/mic, sends SDP `offer`
5. Child receives offer, creates answer, sends it back
6. ICE candidates exchanged → P2P stream established
7. Video/audio streams directly browser-to-browser (no server relay)

---

## 📦 5. Django Apps — Deep Dive

### 5.1 `apps/users` — Authentication & User Management

**Purpose**: Core auth, registration, login, profile management, dashboards, analytics

**Models** (`models.py`):
- `CustomUser` — extends Django's `AbstractUser`. Email is the login field. Has a `role` field (teacher/child/parent/therapist)
- `TeacherProfile` — links to CustomUser 1:1, has `assigned_children` (M2M to ChildProfile)
- `ChildProfile` — has `age`, `diagnosis_info`, `learning_level`, `primary_teacher` (FK to TeacherProfile)
- `ParentProfile` — has `assigned_children` (M2M to ChildProfile)
- `ParentDevice` — stores `fcm_token` for push notifications per parent device

**Views** (`views.py` — 43 KB, largest file):
- `login_view` — Email + password login, redirects by role
- `register_view` — Creates user + role-specific profile in one step
- `dashboard_view` — Detects role, collects statistics, renders correct dashboard template
- `profile_view` — Edit profile info and picture
- `analytics_view` — Teacher analytics: student progress, activity feed, KPI cards
- `notifications_view` — Lists all notifications for current user
- `user_detail_view` — Teacher views individual student detail

**URLs** (`urls.py`): login, logout, register, dashboard, profile, analytics, user-list, user-detail, reports, settings, notifications

**Templates**: `login.html`, `register.html`, `dashboard_teacher.html`, `dashboard_child.html`, `dashboard_parent.html`, `analytics.html`, `profile.html`, `students.html`, `user_detail.html`, `reports.html`, `settings.html`, `notifications.html`

---

### 5.2 `apps/learning` — Learning Modules

**Purpose**: Alphabet, number, word, and emotion learning. Progress tracking. Integration with external React-based learning iframes.

**Models** (`models.py`):
- `Letter` — stores A-Z, image, case (upper/lower), optional `tracing_data` (JSONField)
- `Number` — stores 0-20, image, quantity image
- `Word` — text, image, category (animal/food/color/emotion/custom), created_by
- `Emotion` — name, video file, is_active (used in emotion recognition module)
- `ChildLetterProgress` — tracks which letters a child has completed (unique per child+letter)
- `ChildNumberProgress` — tracks number completion
- `ChildWordProgress` — tracks word completion
- `ChildEmotionProgress` — tracks emotion completion
- `Achievement` — milestone badges (name, description, achieved_on) per child
- `LearningProgress` — **Generic model** used by React iframe apps. Stores `(user, module, item)` tuples e.g. `('alice', 'alphabet', 'A')`

**Views** (`views.py`):
- `learning_dashboard` — Shows all module tiles with completion %
- `alphabet_learning` — Passes letters + child's completed letters to template
- `number_learning` — Same for numbers
- `word_learning` — Same for words
- `emotion_learning` — Lists emotion videos
- API views for React apps to POST/GET progress data

**Key Integration** (`learning_iframe_bridge.js`):
- Django page embeds a React app in an `<iframe>`
- Bridge script sends `COMPLETED_ITEMS` from Django context to the iframe via `postMessage`
- Iframe sends back `restore_progress` / `mark_complete` messages
- Bridge relays completions to the Django REST API

---

### 5.3 `apps/routines` — Visual Schedules & Reminders

**Purpose**: Therapists/teachers create structured daily routines for children. Parents receive push notifications when routine time arrives.

**Models** (`models.py`):
- `Routine` — title, description, created_by (teacher/therapist), child (OneToOne), is_active
- `Task` — belongs to Routine. Has title, image, order, estimated_duration (minutes), is_required
- `TaskCompletion` — records when a child completed a task (timestamp, who marked it)
- `RoutineSchedule` — which day of week + time a routine runs for a given child
- `TimetableEntry` — structured daily timetable (sleep, wake_up, food, school_time, etc.)
- `ChildRoutine` — simplified routine with `repeat_days` (comma-separated ints) and `notify_parent` flag

**Background Task** (`tasks.py` + Celery Beat):
- Every minute, `check_and_send_routine_notifications` runs
- Finds `ChildRoutine` records matching current hour:minute and day
- Calls `send_push_notification()` for child's devices and parent's devices

**Notifications** (`notifications.py`):
- Uses `firebase-admin` SDK
- `initialize_firebase()` — lazy-loads Firebase using `serviceAccountKey.json`
- `send_push_notification(token, title, body, data)` — sends FCM message

---

### 5.4 `apps/games` — Educational Games

**Purpose**: Gamified skill-building for children — color matching and animal matching.

**Models** (`models.py`):
- `Game` — base game record (name, description, is_active)
- `ColorMatchingGame` — level, time_limit, points_per_match, required_matches
- `Color` — name, hex_code, category (primary/secondary/warm/cool/neutral)
- `ColorMatchingLevel` — links a ColorMatchingGame to a set of Colors + grid_size config
- `Animal` — name, image (for animal matching)
- `AnimalMatchingLevel` — level config (how many animals to match)
- `GameSession` — per-play session: child, game, level, score, time_taken, completed
- `ColorMatchingSession` — extended session data: matches_found, total_attempts, accuracy
- `AnimalMatchingSession` — matches_found, total_attempts
- `GameProgress` — aggregate progress: highest_level_completed, total_score, average_accuracy, last_played

**Views**: Serve game pages, accept score submission, return level configs via AJAX

---

### 5.5 `apps/drawing` — Canvas Drawing Tool

**Purpose**: Children express creativity via a free-draw canvas. Drawings can be shared with parents/teachers/therapists.

**Models** (`models.py`):
- `Drawing` — title, child (FK), canvas_data (JSONField), canvas dimensions, sharing flags (shared_with_parents/therapists/teachers), version_number, parent_drawing (self-FK for versioning)
- `DrawingSession` — analytics per drawing session: strokes_count, colors_used (JSONField), tools_used (JSONField), duration_seconds

**Key Methods on Drawing**:
- `can_be_viewed_by(user)` — Role-based permission check
- `create_new_version()` — Saves a new version of the drawing
- `get_canvas_data()` / `set_canvas_data()` — JSON serialization helpers

**Frontend** (`drawing_canvas.js`):
- HTML5 Canvas 2D API for free drawing
- Supports: pen, eraser, color picker, brush size, undo, save
- Saves canvas state as JSON to Django via AJAX POST

---

### 5.6 `apps/messaging` — Real-time Chat + Video Calls

**Purpose**: Teacher ↔ Parent / Teacher ↔ Child real-time communication.

**Models** (`models.py`):
- `Message` — sender (FK), receiver (FK), content, timestamp, is_read

**WebSocket Consumer** (`consumers.py`):
- `VideoCallConsumer(AsyncWebsocketConsumer)` — handles WebRTC signaling
- On connect: creates room group `video_call_{id1}_{id2}` (sorted user IDs = same room for both)
- Relays all signals (call-request, call-accepted, offer, answer, ice candidates) between the two participants
- Does NOT send messages back to the sender (filters by `sender_id`)

**Routing** (`routing.py`):
- WebSocket URL: `ws/call/<int:user_id>/`

**Frontend** (`webrtc_call.js` — 542 lines):
- Implements the complete WhatsApp-style call flow
- State machine: `idle → outgoing → incoming → active`
- ICE candidate queuing to handle race conditions
- Mic/camera toggle with live `media-status` signal to remote peer

---

### 5.7 `apps/communication` — AAC Board

**Purpose**: Augmentative and Alternative Communication — picture-based symbol board for non-verbal children.

**Models** (`models.py`):
- `AACCategory` — name, icon (Material Icon name), color code, display order
- `AACSymbol` — word, image, audio file, action_description, color_code, is_quick_need, order. Belongs to a category.

**Views** (`views.py`):
- `aac_dashboard` — Loads all categories + "quick need" symbols (Zone 1)
- `aac_category_detail` — Symbols in a specific category
- `aac_learning_mode` — Practice mode for a specific symbol
- `aac_type_mode` — Keyboard-style input mode

**Frontend** (`aac_shared.js`):
- Uses **Web Speech API** (`window.speechSynthesis`) to speak selected symbols aloud
- Supports building sentences by tapping symbol cards

---

## 🗄️ 6. Database Schema (All Models Summary)

```
CustomUser (users)
  ├── TeacherProfile (1:1)
  │     └── assigned_children → ChildProfile (M2M)
  ├── ChildProfile (1:1)
  │     └── primary_teacher → TeacherProfile (FK)
  ├── ParentProfile (1:1)
  │     └── assigned_children → ChildProfile (M2M)
  └── ParentDevice (1:Many) — FCM tokens

Routine (routines)
  ├── Task (1:Many)
  │     └── TaskCompletion (1:Many)
  └── RoutineSchedule (1:Many)
  TimetableEntry (FK → Routine)
  ChildRoutine (FK → CustomUser[child])

Letter / Number / Word / Emotion (learning)
  ChildLetterProgress / ChildNumberProgress / ChildWordProgress / ChildEmotionProgress
  LearningProgress (generic, used by React apps)
  Achievement (FK → CustomUser)

Game / ColorMatchingGame / Animal (games)
  Color ← ColorMatchingLevel → ColorMatchingGame
  AnimalMatchingLevel
  GameSession → ColorMatchingSession / AnimalMatchingSession
  GameProgress

Drawing (drawing)
  └── DrawingSession (1:Many)

Message (messaging) — sender/receiver FK to CustomUser

AACCategory (communication)
  └── AACSymbol (1:Many)
```

---

## 🌐 7. URL Routing

| URL Prefix | App | Key Pages |
|------------|-----|-----------|
| `/` | — | Redirects to `/login/` |
| `/login/`, `/logout/`, `/register/` | `users` | Auth pages |
| `/dashboard/` | `users` | Role-based dashboard |
| `/profile/` | `users` | User profile edit |
| `/analytics/` | `users` | Teacher analytics |
| `/students/` | `users` | Student list |
| `/user/<id>/` | `users` | Student detail |
| `/routines/` | `routines` | Visual schedules |
| `/games/` | `games` | Game hub |
| `/learning/` | `learning` | Learning module hub |
| `/drawing/` | `drawing` | Canvas drawing |
| `/messaging/` | `messaging` | Chat & video call |
| `/communication/` | `communication` | AAC board |
| `/admin/` | Django Admin | Full database admin |
| `ws/call/<id>/` | `messaging` | WebSocket (WebRTC) |

---

## ⚙️ 8. Configuration & Settings

### Installed Apps (settings.py)
```python
INSTALLED_APPS = [
    'daphne',            # ASGI server for WebSockets
    # Django defaults...
    'rest_framework',    # DRF
    'corsheaders',       # CORS
    'channels',          # WebSocket support
    # Local apps...
    'apps.users', 'apps.routines', 'apps.learning',
    'apps.drawing', 'apps.games', 'apps.messaging', 'apps.communication',
]
```

### Key Settings
| Setting | Value | Purpose |
|---------|-------|---------|
| `AUTH_USER_MODEL` | `'users.CustomUser'` | Custom email-based user |
| `USERNAME_FIELD` | `'email'` | Login with email, not username |
| `CHANNEL_LAYERS` | Redis @ `127.0.0.1:6379` | WebSocket message broker |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery task queue broker |
| `SESSION_COOKIE_AGE` | `3600` (1 hour) | Session timeout |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | `True` | Auto logout on browser close |
| `MEDIA_ROOT` | `BASE_DIR/media` | Uploaded files location |
| `STATIC_ROOT` | `BASE_DIR/staticfiles` | Collected static files |

### Celery Beat Schedule
```python
'check-routine-notifications-every-minute': {
    'task': 'apps.routines.tasks.check_and_send_routine_notifications',
    'schedule': crontab(minute='*'),  # Every minute
}
```

---

## 🚀 9. How to Run the Application

### Prerequisites
```bash
# Ensure you have Python 3.8+ and Redis installed
redis-server   # Redis must be running for WebSockets + Celery
```

### Setup (First Time)
```bash
# 1. Navigate to project folder
cd /Users/gmk/Projects/Neuro_WebApp-main

# 2. Activate virtual environment
source env/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. (Optional) Create superuser
python manage.py createsuperuser
```

### Run (Every Time)
```bash
# Terminal 1: Start Django development server
source env/bin/activate
python manage.py runserver 127.0.0.1:8000

# Terminal 2 (optional): Start Celery worker for background notifications
source env/bin/activate
celery -A neurolearn worker --loglevel=info

# Terminal 3 (optional): Start Celery Beat for scheduled tasks
source env/bin/activate
celery -A neurolearn beat --loglevel=info
```

> **Note**: WebSockets (video calls, real-time chat) require **Redis** to be running. Without Redis, only HTTP features work.

---

## 🔐 10. Authentication System

- **Login field**: Email (not username)
- **Custom model**: `CustomUser` extends Django's `AbstractUser`
- **Session-based auth**: Django's built-in session middleware
- **Role detection**: `request.user.role` checked in every dashboard view
- **Access control**: Views use `@login_required` decorator + role checks to prevent unauthorized access
- **Password validators**: Disabled in current dev config (any password accepted at registration)
- **Profile pictures**: Uploaded via `Pillow` → stored in `media/profile_pics/`

---

## 📱 11. Push Notifications (Firebase FCM)

1. **Client side** (`fcm_registration.js`): Registers the browser with Firebase Service Worker, gets FCM token
2. **Token storage**: Sent to backend → stored in `ParentDevice` model (linked to the parent user)
3. **Trigger**: Celery Beat runs every minute → `check_and_send_routine_notifications` task
4. **Sending** (`notifications.py`): Uses `firebase-admin` to send FCM messages to stored device tokens
5. **Targets**: Both the child's devices AND the parent's devices receive the notification

> **Requirement**: `serviceAccountKey.json` from Firebase Console must be placed in the project root for notifications to work.

---

## 📊 12. Feature Completion Summary

| Feature | Status | Module |
|---------|--------|--------|
| User auth (email login) | ✅ Complete | `users` |
| Role-based dashboards | ✅ Complete | `users` |
| Profile management | ✅ Complete | `users` |
| Teacher analytics | ✅ Complete | `users` |
| Visual routine schedules | ✅ Complete | `routines` |
| Task completion tracking | ✅ Complete | `routines` |
| Push notifications (FCM) | ✅ Complete | `routines` + Firebase |
| Alphabet learning | ✅ Complete | `learning` |
| Number learning | ✅ Complete | `learning` |
| Word learning | ✅ Complete | `learning` |
| Emotion learning | ✅ Complete | `learning` |
| Progress tracking (learning) | ✅ Complete | `learning` |
| Color matching game | ✅ Complete | `games` |
| Animal matching game | ✅ Complete | `games` |
| Canvas drawing tool | ✅ Complete | `drawing` |
| Drawing versioning | ✅ Complete | `drawing` |
| Real-time messaging (WebSocket) | ✅ Complete | `messaging` |
| WebRTC video calls | ✅ Complete | `messaging` |
| AAC communication board | ✅ Complete | `communication` |
| Text-to-speech (AAC) | ✅ Complete | `communication` + Web Speech API |
| REST API (for React iframes) | ✅ Complete | DRF + `learning` |
| Admin interface | ✅ Complete | Django Admin |

---

## 🧩 13. Key Design Decisions

1. **Email as login field** — More accessible than usernames for parents; enforced by `USERNAME_FIELD = 'email'`
2. **Single dashboard URL `/dashboard/`** — Role detection happens in the view, not routing; reduces URL complexity
3. **React learning apps inside iframes** — Allows independent learning apps while keeping Django as the auth/progress layer; bridge via `postMessage`
4. **WebRTC P2P video with WebSocket signaling** — Server only relays SDP/ICE signals; actual video is peer-to-peer (low latency, no server media processing)
5. **JSONField for canvas data** — Stores entire drawing state as JSON; supports versioning via `parent_drawing` self-FK
6. **Celery + Redis for notifications** — Decouples notification delivery from HTTP request cycle; handles time-based triggers reliably
7. **SQLite for dev** — Zero-config for development; ORM abstraction makes switching to PostgreSQL in production easy

---

*Notes prepared for NEURO Learning Platform — 4-member group project | Project evaluation: May 2026*
