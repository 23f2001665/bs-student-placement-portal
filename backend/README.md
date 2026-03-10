# Placement Portal Application - Backend

This is the backend for the Placement Portal Application, built using Flask. It provides APIs for managing placements, companies, students, and more.

## Features

- User authentication and authorization
- CRUD operations for placements, companies, and students
- Caching with Redis for improved performance
- Asynchronous tasks with Celery
- Email notifications

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone
    cd placement-portal-backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (e.g., database URI, Redis URL, etc.) to .env file.:

5. Run database migrations:

   ```bash
   flask db upgrade
   ```

6. Start the Flask application:

   ```bash
   flask run
   ```

7. To start the Celery worker for asynchronous tasks:

   ```bash
   celery -A application.celery_app.celery worker --loglevel=info
   ```

8. To start the celery beat for scheduled tasks:

   ```bash
    celery -A application.celery_app.celery beat --loglevel=info
   ```

![dummy image](images/me.jpg)

