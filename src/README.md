# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

The app now persists its core data in a local SQLite database with explicit models for activities, students, and registrations.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```bash
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```bash
   python app.py
   ```

   This will automatically create a local SQLite database file named `activities.db` in `src/` if it does not already exist.

3. Open your browser and go to:
   - API documentation: <http://localhost:8000/docs>
   - Alternative documentation: <http://localhost:8000/redoc>

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application now uses persistent core domain models:

1. **Activities**

   - Description
   - Schedule text
   - Category
   - Maximum number of participants allowed
   - Active status

2. **Students**

   - Email
   - Name
   - Optional grade or year

3. **Registrations**

   - Link one student to one activity
   - Track status for the signup lifecycle

## Persistence Notes

The legacy endpoints remain the same for now, but the data is no longer stored in memory. Default activities are seeded into the database only on first startup.
