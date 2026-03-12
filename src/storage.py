from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).with_name("activities.db")

ACTIVITY_NOT_FOUND = "Activity not found"
STUDENT_NOT_FOUND = "Student not found"
REGISTRATION_NOT_FOUND = "Registration not found"

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


def _serialize_activity(row: sqlite3.Row) -> dict:
    registered_count = row["registered_count"] or 0
    waitlisted_count = row["waitlisted_count"] or 0
    available_spots = row["max_participants"] - registered_count
    if available_spots < 0:
        available_spots = 0

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "schedule_text": row["schedule_text"],
        "location": row["location"],
        "category": row["category"],
        "max_participants": row["max_participants"],
        "registered_count": registered_count,
        "waitlisted_count": waitlisted_count,
        "available_spots": available_spots,
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _serialize_registration(row: sqlite3.Row) -> dict:
    return {
        "id": row["registration_id"],
        "activity_id": row["activity_id"],
        "student": {
            "id": row["student_id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "grade_or_year": row["grade_or_year"],
            "phone_number": row["phone_number"],
            "is_active": bool(row["student_is_active"]),
        },
        "status": row["status"],
        "notes": row["notes"],
        "registered_at": row["registered_at"],
        "updated_at": row["updated_at"],
    }


def _activity_query(include_inactive: bool = False) -> str:
    active_filter = "" if include_inactive else "WHERE a.is_active = 1"
    return f"""
        SELECT
            a.id,
            a.name,
            a.description,
            a.schedule_text,
            a.location,
            a.category,
            a.max_participants,
            a.is_active,
            a.created_at,
            a.updated_at,
            COALESCE(SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END), 0) AS registered_count,
            COALESCE(SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END), 0) AS waitlisted_count
        FROM activities a
        LEFT JOIN registrations r ON r.activity_id = a.id
        {active_filter}
        GROUP BY a.id
    """


def _get_activity_by_id_row(connection: sqlite3.Connection, activity_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            a.id,
            a.name,
            a.description,
            a.schedule_text,
            a.location,
            a.category,
            a.max_participants,
            a.is_active,
            a.created_at,
            a.updated_at,
            COALESCE(SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END), 0) AS registered_count,
            COALESCE(SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END), 0) AS waitlisted_count
        FROM activities a
        LEFT JOIN registrations r ON r.activity_id = a.id
        WHERE a.id = ?
        GROUP BY a.id
        """,
        (REGISTRATION_STATUS_REGISTERED, REGISTRATION_STATUS_WAITLISTED, activity_id),
    ).fetchone()


def _get_activity_id_by_name(connection: sqlite3.Connection, activity_name: str) -> int | None:
    row = connection.execute(
        "SELECT id FROM activities WHERE name = ? AND is_active = 1",
        (activity_name,),
    ).fetchone()
    return row["id"] if row else None


def _get_registration_row(connection: sqlite3.Connection, registration_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            r.id AS registration_id,
            r.activity_id,
            r.status,
            r.notes,
            r.registered_at,
            r.updated_at,
            s.id AS student_id,
            s.email,
            s.full_name,
            s.grade_or_year,
            s.phone_number,
            s.is_active AS student_is_active
        FROM registrations r
        JOIN students s ON s.id = r.student_id
        WHERE r.id = ?
        """,
        (registration_id,),
    ).fetchone()


def list_activities() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            _activity_query() + " ORDER BY a.name",
            (REGISTRATION_STATUS_REGISTERED, REGISTRATION_STATUS_WAITLISTED),
        ).fetchall()

    return [_serialize_activity(row) for row in rows]


def list_activities_for_management() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            _activity_query(include_inactive=True) + " ORDER BY a.is_active DESC, a.name",
            (REGISTRATION_STATUS_REGISTERED, REGISTRATION_STATUS_WAITLISTED),
        ).fetchall()

    return [_serialize_activity(row) for row in rows]


def get_activity(activity_id: int) -> dict:
    with get_connection() as connection:
        row = _get_activity_by_id_row(connection, activity_id)
        if not row or not row["is_active"]:
            raise KeyError(ACTIVITY_NOT_FOUND)

    return _serialize_activity(row)


def create_activity(
    name: str,
    description: str,
    schedule_text: str,
    category: str,
    max_participants: int,
    location: str | None = None,
    is_active: bool = True,
) -> dict:
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO activities (
                    name,
                    description,
                    schedule_text,
                    location,
                    category,
                    max_participants,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    description,
                    schedule_text,
                    location,
                    category,
                    max_participants,
                    1 if is_active else 0,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Activity name already exists") from error

        activity_row = _get_activity_by_id_row(connection, cursor.lastrowid)

    return _serialize_activity(activity_row)


def update_activity(
    activity_id: int,
    name: str,
    description: str,
    schedule_text: str,
    category: str,
    max_participants: int,
    location: str | None = None,
    is_active: bool = True,
) -> dict:
    with get_connection() as connection:
        existing_activity = _get_activity_by_id_row(connection, activity_id)
        if not existing_activity:
            raise KeyError(ACTIVITY_NOT_FOUND)
        if existing_activity["registered_count"] > max_participants:
            raise ValueError("Capacity cannot be lower than current registered count")

        try:
            connection.execute(
                """
                UPDATE activities
                SET name = ?,
                    description = ?,
                    schedule_text = ?,
                    location = ?,
                    category = ?,
                    max_participants = ?,
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name,
                    description,
                    schedule_text,
                    location,
                    category,
                    max_participants,
                    1 if is_active else 0,
                    activity_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Activity name already exists") from error

        activity_row = _get_activity_by_id_row(connection, activity_id)

    return _serialize_activity(activity_row)


def set_activity_active(activity_id: int, is_active: bool) -> dict:
    with get_connection() as connection:
        existing_activity = _get_activity_by_id_row(connection, activity_id)
        if not existing_activity:
            raise KeyError(ACTIVITY_NOT_FOUND)

        connection.execute(
            """
            UPDATE activities
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if is_active else 0, activity_id),
        )
        activity_row = _get_activity_by_id_row(connection, activity_id)

    return _serialize_activity(activity_row)


def list_activity_registrations(activity_id: int) -> list[dict]:
    with get_connection() as connection:
        activity_row = _get_activity_by_id_row(connection, activity_id)
        if not activity_row or not activity_row["is_active"]:
            raise KeyError(ACTIVITY_NOT_FOUND)

        rows = connection.execute(
            """
            SELECT
                r.id AS registration_id,
                r.activity_id,
                r.status,
                r.notes,
                r.registered_at,
                r.updated_at,
                s.id AS student_id,
                s.email,
                s.full_name,
                s.grade_or_year,
                s.phone_number,
                s.is_active AS student_is_active
            FROM registrations r
            JOIN students s ON s.id = r.student_id
            WHERE r.activity_id = ?
            ORDER BY r.registered_at DESC, r.id DESC
            """,
            (activity_id,),
        ).fetchall()

    return [_serialize_registration(row) for row in rows]


def list_student_registrations(student_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                r.id AS registration_id,
                r.activity_id,
                r.status,
                r.notes,
                r.registered_at,
                r.updated_at,
                s.id AS student_id,
                s.email,
                s.full_name,
                s.grade_or_year,
                s.phone_number,
                s.is_active AS student_is_active
            FROM registrations r
            JOIN students s ON s.id = r.student_id
            WHERE s.id = ?
            ORDER BY r.registered_at DESC, r.id DESC
            """,
            (student_id,),
        ).fetchall()
        if not rows:
            student_exists = connection.execute(
                "SELECT id FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            if not student_exists:
                raise KeyError(STUDENT_NOT_FOUND)

    return [_serialize_registration(row) for row in rows]


def list_activities_legacy() -> dict[str, dict]:
    activities: dict[str, dict] = {}
    for activity in list_activities():
        activities[activity["name"]] = {
            "description": activity["description"],
            "schedule": activity["schedule_text"],
            "max_participants": activity["max_participants"],
            "participants": [
                registration["student"]["email"]
                for registration in list_activity_registrations(activity["id"])
                if registration["status"] == REGISTRATION_STATUS_REGISTERED
            ],
        }

    return activities


def register_student_for_activity(activity_id: int, email: str, full_name: str | None = None) -> dict:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        activity = _get_activity_by_id_row(connection, activity_id)
        if not activity or not activity["is_active"]:
            raise KeyError(ACTIVITY_NOT_FOUND)

        student_id = _ensure_student(connection, normalized_email, full_name)
        existing_registration = connection.execute(
            "SELECT id, status FROM registrations WHERE activity_id = ? AND student_id = ?",
            (activity_id, student_id),
        ).fetchone()
        if existing_registration and existing_registration["status"] != REGISTRATION_STATUS_CANCELLED:
            raise ValueError("Student is already registered for this activity")

        if activity["registered_count"] >= activity["max_participants"]:
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
            registration = _get_registration_row(connection, existing_registration["id"])
            return _serialize_registration(registration)

        cursor = connection.execute(
            """
            INSERT INTO registrations (activity_id, student_id, status)
            VALUES (?, ?, ?)
            """,
            (activity_id, student_id, REGISTRATION_STATUS_REGISTERED),
        )
        registration = _get_registration_row(connection, cursor.lastrowid)

    return _serialize_registration(registration)


def cancel_registration(activity_id: int, registration_id: int) -> dict:
    with get_connection() as connection:
        activity = _get_activity_by_id_row(connection, activity_id)
        if not activity or not activity["is_active"]:
            raise KeyError(ACTIVITY_NOT_FOUND)

        registration = connection.execute(
            "SELECT id, status FROM registrations WHERE id = ? AND activity_id = ?",
            (registration_id, activity_id),
        ).fetchone()
        if not registration:
            raise KeyError(REGISTRATION_NOT_FOUND)
        if registration["status"] == REGISTRATION_STATUS_CANCELLED:
            raise ValueError("Registration is already cancelled")

        connection.execute(
            "UPDATE registrations SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (REGISTRATION_STATUS_CANCELLED, registration_id),
        )
        updated_registration = _get_registration_row(connection, registration_id)

    return _serialize_registration(updated_registration)


def signup_student(activity_name: str, email: str) -> None:
    with get_connection() as connection:
        activity_id = _get_activity_id_by_name(connection, activity_name)
    if activity_id is None:
        raise KeyError(ACTIVITY_NOT_FOUND)
    register_student_for_activity(activity_id, email)


def unregister_student(activity_name: str, email: str) -> None:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        activity_id = _get_activity_id_by_name(connection, activity_name)
        if activity_id is None:
            raise KeyError(ACTIVITY_NOT_FOUND)

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

    cancel_registration(activity_id, registration["id"])