# FYP - RAISC - Backend

This is the backend for our FYP application built using Django and Django Channels. It provides APIs and WebSocket support for functionalities such as user authentication, real-time chat, resource management, and appointment scheduling.

## AI Chatbot
Current backend implementation and plan doesn't consider AI Chatbot integration. It would be integrated later on following its individual development
## **Table of Contents**

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Clone the Repository](#clone-the-repository)
  - [Set Up the Virtual Environment](#set-up-the-virtual-environment)
  - [Install Dependencies and Environment Setup](#install-dependencies-and-environment-setup)
  - [Set Up the Database](#set-up-the-database)
  - [Apply Migrations](#apply-migrations)
  - [Create a Superuser](#create-a-superuser)
  - [Run the Development Server](#run-the-development-server)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [WebSocket Endpoints](#websocket-endpoints)
- [Testing the Application](#testing-the-application)
- [Deployment Considerations](#deployment-considerations)
- [License](#license)

---

## **Features**

- **User Authentication**: Supports three user types - Admin, Patient, and Doctor.
- **Token-Based Authentication**: Secure APIs using token authentication.
- **Real-Time Chat**: Anonymous group chats using WebSockets with threaded conversations.
- **Resource Management**: Provides resources based on users' mental conditions.
- **Appointment Scheduling**: Doctors can schedule appointments with patients.
- **Profile Management**: Users have profiles to store additional information.

## **Tech Stack**

- **Backend Framework**: Django
- **WebSockets**: Django Channels
- **Real-Time Communication**: Redis
- **REST API**: Django REST Framework
- **Database**: PostgreSQL
- **Caching and Sessions**: Redis (Optional)
- **Python Version**: Python 3.x

## **Prerequisites**

- **Python 3.x** installed on your machine.
- **Virtual environment** tool (optional but recommended).
- **PostgreSQL** installed and running.
- **Redis** installed and running.

## **Installation**

### **Clone the Repository**

```bash
git clone https://github.com/hammad-ahmed-01/RAISC_backend.git
cd RAISC_backend
```
## **Install Dependencies and Environment Setup**
```bash
pip install -r requirements.txt
```
create a .evn file and add to .gitignore
```bash
# .env file

# Django settings
SECRET_KEY=your-secret-key
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
POSTGRES_DB=RAISC_backend
POSTGRES_USER=your_postgres_username
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
```
## **Set Up the Database**
If you haven't installed PostgreSQL, download it from the official website or use your operating system's package manager.
<br>
Create the Database 'RAISC_backend'
<br><br>
**Start Redis Server !! Skip for now**

## **Apply Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

## **Create a Superuser**
```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password.

## **Run the Development Server**
```bash
python manage.py runserver
```

## **Project Structure**
**RAISC_backend/:** Main project directory containing settings and URLs.<br>
**users/:** Handles user authentication and profiles.<br>
**chat/:** Manages real-time chat functionality with threaded conversations.<br>
**resources/:** Provides resource-related APIs.<br>
**appointments/:** Manages appointment scheduling.<br>
```bash
RAISC_backend/
├── manage.py
├── RAISC_backend/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── chat/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py
│   ├── models.py
│   ├── routing.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── resources/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── appointments/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/
│   └── (if needed)
├── static/
│   └── (if needed)
├── .env
├── requirements.txt
└── README.md
```
## **API Endpoints**
**Current Level!!**<br>
**Users**<br>
Register: POST /api/users/register/<br>
Login: POST /api/users/login/<br>
User Detail: GET /api/users/me/<br>
**Resources**<br>
List Resources: GET /api/resources/<br>
**Appointments**<br>
List/Create Appointments: GET/POST /api/appointments/<br>
**Chat**<br>
List Chat Groups: GET /api/chat/groups/<br>
List/Create Questions: GET/POST /api/chat/groups/<group_id>/questions/<br>
List/Create Messages: GET/POST /api/chat/questions/<question_id>/messages/<br>

## **WebSocket Endpoints**
**Chat Thread:**
ws://127.0.0.1:8000/ws/chat/<group_id>/<question_id>/

<br><br>
**Current ReadME is incomplete!!**
