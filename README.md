# Event System

Event System is a full-stack web application for creating, approving, booking, and managing events. It supports attendee bookings, QR-based tickets, organizer attendee management, booking cancellation rules, and reminder emails before an event starts.

## Features

- User registration and login with JWT authentication
- Google sign-in support
- Password reset by email
- Student verification flow with discounted ticket pricing
- Event creation, editing, approval, and deletion
- Event browsing with category filters and recommendations
- Ticket booking and payment flow
- QR ticket generation and ticket email delivery
- Booking cancellation allowed only more than 3 hours before the event
- Organizer attendee list and CSV export
- Manual reminder emails from the organizer event page
- Automatic reminder emails 12 hours before the event
- Ticket scanning and check-in support
- Admin dashboard for approvals, reviews, bookings, and attendance

## Tech Stack

- Frontend: React, Vite, Tailwind CSS, React Router
- Backend: Django, Django REST Framework, SimpleJWT
- Database: PostgreSQL
- Other tools: Pillow, QRCode, dotenv

## Project Structure

```text
event-system/
├── backend/      # Django backend
├── docs/         # Project diagrams and documentation
├── frontend/     # React frontend
├── README.md
└── package.json  # Root helper scripts
```

## Documentation

- PlantUML activity diagrams: [docs/activity-diagrams-plantuml.md](docs/activity-diagrams-plantuml.md)
- PlantUML database ERD: [docs/database-erd.puml](docs/database-erd.puml)

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:hekka10/event-system.git
cd event-system
```

### 2. Install backend dependencies

If you are using the project virtual environment:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Install frontend dependencies

```bash
npm install --prefix frontend
```

You can also use the root helper script:

```bash
npm run install:all
```

## Environment Setup

Create a `.env` file inside `backend/` if needed. The app reads environment variables for database, email, and frontend/backend URLs.

Common variables:

```env
DB_NAME=event_system
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433

FRONTEND_BASE_URL=http://localhost:5173
BACKEND_BASE_URL=http://127.0.0.1:8000

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-email@gmail.com

EVENT_REMINDER_LEAD_HOURS=12
```

## Database Setup

Run migrations before starting the project:

```bash
python backend/manage.py migrate
```

## Running the Project

### Run backend

```bash
python backend/manage.py runserver
```

### Run frontend

```bash
npm run dev --prefix frontend
```

### Run both from the root

```bash
npm run dev
```

## Main Workflows

### Booking Cancellation Rule

Confirmed or pending bookings can only be cancelled more than 3 hours before the event start time.

### Organizer Attendee Management

Organizers can:

- view confirmed attendees for their event
- export attendee data as CSV
- send manual reminder emails

### Automatic Reminder Emails

Automatic reminders are sent to confirmed attendees before an event starts.

Default reminder time:

- 12 hours before the event

Run the reminder command manually:

```bash
python backend/manage.py send_event_reminders
```

Preview how many reminders are due:

```bash
python backend/manage.py send_event_reminders --dry-run
```

For true automation, schedule the command with cron or your hosting scheduler. Example:

```bash
*/15 * * * * cd /path/to/event-system && /path/to/python backend/manage.py send_event_reminders
```

## Testing

Run all backend tests:

```bash
python backend/manage.py test
```

Run frontend build:

```bash
npm run build --prefix frontend
```

Run frontend lint:

```bash
npm run lint --prefix frontend
```

## API Overview

Main API groups:

- `/api/auth/` for authentication and password reset
- `/api/events/` for event CRUD, approval, attendees, and reminders
- `/api/bookings/` for bookings, cancellation, tickets, and scanning
- `/api/payments/` for payment operations
- `/api/dashboard/stats/` for admin dashboard data

## Submission Summary

This project includes the following completed assignment features:

- authentication and password reset
- event management
- student discount verification
- booking and ticket generation
- 3-hour cancellation restriction
- organizer attendee export
- manual reminder emails
- automatic reminder emails 12 hours before event start
