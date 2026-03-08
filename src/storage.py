from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).with_name("activities.db")

REGISTRATION_STATUS_REGISTERED = "registered"
REGISTRATION_STATUS_WAITLISTED = "waitlisted"
REGISTRATION_STATUS_CANCELLED = "cancelled"


DEFAULT_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule_text": "Fridays, 3:30 PM - 5:00 PM",
        "category": "club",
        "location": None,
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule_text": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "category": "class",
        "location": None,
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule_text": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "category": "class",
        "location": None,
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule_text": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "category": "team",
        "location": None,
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule_text": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "category": "team",
        "location": None,
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule_text": "Thursdays, 3:30 PM - 5:00 PM",
        "category": "club",
        "location": None,
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule_text": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "category": "club",
        "location": None,
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule_text": "Tuesdays, 3:30 PM - 4:30 PM",
        "category": "club",
        "location": None,
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule_text": "Fridays, 4:00 PM - 5:30 PM",
        "category": "team",
        "location": None,
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                grade_or_year TEXT,
                phone_number TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule_text TEXT NOT NULL,
                location TEXT,
                category TEXT NOT NULL,
                max_participants INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'registered' CHECK(status IN ('registered', 'waitlisted', 'cancelled')),
                notes TEXT,
                registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(activity_id, student_id),
                FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            """
        )
        _seed_default_data(connection)


def _seed_default_data(connection: sqlite3.Connection) -> None:
    existing_count = connection.execute("SELECT COUNT(*) AS count FROM activities").fetchone()["count"]
    if existing_count:
        return

    for activity in DEFAULT_ACTIVITIES:
        cursor = connection.execute(
            """
            INSERT INTO activities (name, description, schedule_text, location, category, max_participants)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                activity["name"],
                activity["description"],
                activity["schedule_text"],
                activity["location"],
                activity["category"],
                activity["max_participants"],
            ),
        )
        activity_id = cursor.lastrowid

        for email in activity["participants"]:
            student_id = _ensure_student(connection, email)
            connection.execute(
                """
                INSERT INTO registrations (activity_id, student_id, status)
                VALUES (?, ?, ?)
                """,
                (activity_id, student_id, REGISTRATION_STATUS_REGISTERED),
            )


def _ensure_student(connection: sqlite3.Connection, email: str, full_name: str | None = None) -> int:
    normalized_email = email.strip().lower()
    row = connection.execute(
        "SELECT id, full_name FROM students WHERE email = ?",
        (normalized_email,),
    ).fetchone()
    if row:
        if full_name and not row["full_name"]:
            connection.execute(
                "UPDATE students SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (full_name, row["id"]),
            )
        return row["id"]

    cursor = connection.execute(
        """
        INSERT INTO students (email, full_name)
        VALUES (?, ?)
        """,
        (normalized_email, full_name or _full_name_from_email(normalized_email)),
    )
    return cursor.lastrowid


def _full_name_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    return " ".join(part.capitalize() for part in local_part.replace(".", " ").replace("_", " ").split())


def list_activities_legacy() -> dict[str, dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                a.id,
                a.name,
                a.description,
                a.schedule_text,
                a.max_participants,
                s.email
            FROM activities a
            LEFT JOIN registrations r
                ON r.activity_id = a.id AND r.status = ?
            LEFT JOIN students s
                ON s.id = r.student_id
            WHERE a.is_active = 1
            ORDER BY a.name, s.email
            """,
            (REGISTRATION_STATUS_REGISTERED,),
        ).fetchall()

    activities: dict[str, dict] = {}
    for row in rows:
        name = row["name"]
        if name not in activities:
            activities[name] = {
                "description": row["description"],
                "schedule": row["schedule_text"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
        if row["email"]:
            activities[name]["participants"].append(row["email"])

    return activities


def signup_student(activity_name: str, email: str) -> None:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        activity = connection.execute(
            "SELECT id, max_participants FROM activities WHERE name = ? AND is_active = 1",
            (activity_name,),
        ).fetchone()
        if not activity:
            raise KeyError("Activity not found")

        student_id = _ensure_student(connection, normalized_email)
        existing_registration = connection.execute(
            "SELECT id, status FROM registrations WHERE activity_id = ? AND student_id = ?",
            (activity["id"], student_id),
        ).fetchone()
        if existing_registration and existing_registration["status"] != REGISTRATION_STATUS_CANCELLED:
            raise ValueError("Student is already signed up")

        registered_count = connection.execute(
            "SELECT COUNT(*) AS count FROM registrations WHERE activity_id = ? AND status = ?",
            (activity["id"], REGISTRATION_STATUS_REGISTERED),
        ).fetchone()["count"]
        if registered_count >= activity["max_participants"]:
            raise OverflowError("Activity is full")

        if existing_registration:
            connection.execute(
                """
                UPDATE registrations
                SET status = ?, updated_at = CURRENT_TIMESTAMP, registered_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (REGISTRATION_STATUS_REGISTERED, existing_registration["id"]),
            )
            return

        connection.execute(
            """
            INSERT INTO registrations (activity_id, student_id, status)
            VALUES (?, ?, ?)
            """,
            (activity["id"], student_id, REGISTRATION_STATUS_REGISTERED),
        )


def unregister_student(activity_name: str, email: str) -> None:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        registration = connection.execute(
            """
            SELECT r.id
            FROM registrations r
            JOIN activities a ON a.id = r.activity_id
            JOIN students s ON s.id = r.student_id
            WHERE a.name = ?
              AND s.email = ?
              AND r.status = ?
            """,
            (activity_name, normalized_email, REGISTRATION_STATUS_REGISTERED),
        ).fetchone()
        if not registration:
            raise ValueError("Student is not signed up for this activity")

        connection.execute(
            "UPDATE registrations SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (REGISTRATION_STATUS_CANCELLED, registration["id"]),
        )