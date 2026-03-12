# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

The app persists its core data in a local SQLite database with explicit models for activities, students, and registrations.

## Features

- View all available extracurricular activities
- Sign up for activities
- Unregister students using stable registration records in the normalized API

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

The app currently exposes both a legacy compatibility API and a normalized API.

### Legacy compatibility endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with their details and current participant count |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student from an activity |

### Normalized registration endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/activities` | List activities with stable IDs and availability counts |
| GET | `/api/activities/{activity_id}` | Get one activity by ID |
| GET | `/api/activities/{activity_id}/registrations` | List registrations for an activity |
| POST | `/api/activities/{activity_id}/registrations` | Create a registration using a JSON request body |
| DELETE | `/api/activities/{activity_id}/registrations/{registration_id}` | Cancel a registration by ID |
| GET | `/api/students/{student_id}/registrations` | List registrations for one student |

Example registration request body:

```json
{
   "email": "student@mergington.edu",
   "full_name": "Student Name"
}
```

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

Default activities are seeded into the database only on first startup. The legacy endpoints remain available for backward compatibility, while the static frontend now uses the normalized API endpoints for listing activities, creating registrations, and cancelling registrations.
