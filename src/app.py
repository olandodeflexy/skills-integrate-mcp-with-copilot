"""High School Management System API."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

from storage import (
    cancel_registration,
    create_activity,
    get_activity,
    initialize_database,
    list_activities,
    list_activities_for_management,
    list_activities_legacy,
    list_activity_registrations,
    list_student_registrations,
    register_student_for_activity,
    set_activity_active,
    signup_student,
    update_activity,
    unregister_student,
)

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

initialize_database()


class RegistrationCreateRequest(BaseModel):
    email: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None


class ActivityUpsertRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    schedule_text: str = Field(min_length=3, max_length=120)
    location: Optional[str] = Field(default=None, max_length=120)
    category: str = Field(min_length=3, max_length=40)
    max_participants: int = Field(ge=1, le=500)
    is_active: bool = True

    @field_validator("name", "description", "schedule_text", "category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None


def _detail_from_exception(error: Exception) -> str:
    if isinstance(error, KeyError) and error.args:
        return str(error.args[0])
    return str(error)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return list_activities_legacy()


@app.get("/api/activities")
def get_normalized_activities():
    return {"activities": list_activities()}


@app.get("/api/management/activities")
def get_management_activities():
    return {"activities": list_activities_for_management()}


@app.post(
    "/api/management/activities",
    status_code=201,
    responses={400: {"description": "Invalid activity request"}},
)
def create_managed_activity(payload: ActivityUpsertRequest):
    try:
        activity = create_activity(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Created activity {activity['name']}",
        "activity": activity,
    }


@app.put(
    "/api/management/activities/{activity_id}",
    responses={400: {"description": "Invalid activity request"}, 404: {"description": "Activity not found"}},
)
def update_managed_activity(activity_id: int, payload: ActivityUpsertRequest):
    try:
        activity = update_activity(activity_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Updated activity {activity['name']}",
        "activity": activity,
    }


@app.post(
    "/api/management/activities/{activity_id}/archive",
    responses={404: {"description": "Activity not found"}},
)
def archive_managed_activity(activity_id: int):
    try:
        activity = set_activity_active(activity_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Archived activity {activity['name']}",
        "activity": activity,
    }


@app.post(
    "/api/management/activities/{activity_id}/restore",
    responses={404: {"description": "Activity not found"}},
)
def restore_managed_activity(activity_id: int):
    try:
        activity = set_activity_active(activity_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Restored activity {activity['name']}",
        "activity": activity,
    }


@app.get(
    "/api/activities/{activity_id}",
    responses={404: {"description": "Activity not found"}},
)
def get_activity_detail(activity_id: int):
    try:
        return get_activity(activity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc


@app.get(
    "/api/activities/{activity_id}/registrations",
    responses={404: {"description": "Activity not found"}},
)
def get_activity_registration_list(activity_id: int):
    try:
        return {
            "activity": get_activity(activity_id),
            "registrations": list_activity_registrations(activity_id),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc


@app.post(
    "/api/activities/{activity_id}/registrations",
    status_code=201,
    responses={400: {"description": "Invalid registration request"}, 404: {"description": "Activity not found"}},
)
def create_registration(activity_id: int, payload: RegistrationCreateRequest):
    try:
        registration = register_student_for_activity(activity_id, payload.email, payload.full_name)
        activity = get_activity(activity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc
    except OverflowError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Registered {registration['student']['email']} for {activity['name']}",
        "registration": registration,
        "activity": activity,
    }


@app.delete(
    "/api/activities/{activity_id}/registrations/{registration_id}",
    responses={400: {"description": "Invalid cancellation request"}, 404: {"description": "Resource not found"}},
)
def delete_registration(activity_id: int, registration_id: int):
    try:
        registration = cancel_registration(activity_id, registration_id)
        activity = get_activity(activity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {
        "message": f"Cancelled registration {registration_id} for {activity['name']}",
        "registration": registration,
        "activity": activity,
    }


@app.get(
    "/api/students/{student_id}/registrations",
    responses={404: {"description": "Student not found"}},
)
def get_student_registration_list(student_id: int):
    try:
        return {"registrations": list_student_registrations(student_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc


@app.post(
    "/activities/{activity_name}/signup",
    responses={400: {"description": "Invalid signup request"}, 404: {"description": "Activity not found"}},
)
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    try:
        signup_student(activity_name, email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc
    except OverflowError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete(
    "/activities/{activity_name}/unregister",
    responses={400: {"description": "Invalid unregister request"}, 404: {"description": "Activity not found"}},
)
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    try:
        unregister_student(activity_name, email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=_detail_from_exception(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail_from_exception(exc)) from exc

    return {"message": f"Unregistered {email} from {activity_name}"}
