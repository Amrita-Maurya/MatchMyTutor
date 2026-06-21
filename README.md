# MatchMyTutor

A full-stack peer tutoring platform built with Django that connects students with tutors based on subjects, availability, and ratings.

MatchMyTutor allows students to discover tutors, book learning sessions, manage schedules, leave reviews, and receive real-time updates. The platform includes REST APIs, PostgreSQL support, email notifications, and WebSocket-powered live notifications.

---

## Features

### User Management
- Student and Tutor registration
- Secure authentication and login system
- Role-based dashboards
- User profile management

### Tutor Features
- Manage teaching subjects
- Set availability slots
- View upcoming sessions
- Receive real-time booking notifications
- Public tutor profiles with ratings and reviews

### Student Features
- Search and discover tutors
- Filter tutors by subject and rating
- Book tutoring sessions
- View and manage bookings
- Leave reviews after completed sessions

### Booking System
- Session scheduling
- Booking confirmation workflow
- Booking cancellation with automatic slot release
- Upcoming session tracking

### Reviews & Ratings
- Star-based rating system
- Tutor review history
- Average rating calculation
- Review eligibility based on completed sessions

### Smart Tutor Matching
- Subject-based matching
- Rating-based ranking
- Search and filtering support
- Sorting by reviews and ratings

### REST API
- Tutor API endpoints
- Booking API endpoints
- Filtering, searching, and pagination
- Authentication and permissions

### Real-Time Notifications
- Django Channels integration
- WebSocket support
- Instant booking notifications
- Instant cancellation notifications

### Email Notifications
- Welcome emails
- Booking confirmations
- Cancellation alerts

---

## Tech Stack

### Backend
- Python
- Django
- Django REST Framework
- Django Channels

### Database
- PostgreSQL
- SQLite (development fallback)

### Frontend
- HTML
- CSS
- JavaScript

### Deployment & Infrastructure
- Daphne (ASGI Server)
- Gunicorn
- WebSockets
- Environment Variable Configuration

---

## Project Structure

```text
MatchMyTutor/
│
├── mystite/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── peer_tutor/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   ├── filters.py
│   │   └── pagination.py
│   │
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── consumers.py
│   ├── routing.py
│   └── email_utils.py
│
├── requirements.txt
├── README.md
└── manage.py
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/<your-username>/MatchMyTutor.git
cd MatchMyTutor
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=

EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=587
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Admin User

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit:

```text
http://127.0.0.1:8000
```

---

## API Highlights

Example endpoints:

```text
/api/tutors/
/api/bookings/
/api/reviews/
```

Supported features:

- Pagination
- Search
- Ordering
- Filtering
- Authentication

Example:

```text
/api/tutors/?subject=Python&min_rating=4
```

---

## Future Enhancements

- AI-powered tutor recommendations
- Video call integration
- In-app chat system
- Payment gateway integration
- Session attendance tracking
- Tutor analytics dashboard
- Mobile application

---

## Key Learning Outcomes

Through this project I gained experience with:

- Full-stack web development
- Django architecture
- Relational database design
- REST API development
- Authentication and authorization
- Real-time communication using WebSockets
- PostgreSQL integration
- Deployment workflows
- Git and GitHub collaboration

---

## Author

**Amrita Maurya**

GitHub: https://github.com/Amrita-Maurya
