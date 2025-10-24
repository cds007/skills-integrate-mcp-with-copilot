"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
import re
from pydantic import BaseModel, EmailStr


a = 1

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Load activities from JSON file when present, otherwise fall back to embedded defaults
activities_file = current_dir / "activities.json"
if activities_file.exists():
    try:
        with open(activities_file, "r", encoding="utf-8") as f:
            activities = json.load(f)
    except Exception:
        # If the JSON is malformed, fall back to an empty dict and surface errors via endpoints
        activities = {}
else:
    # Embedded defaults (fallback)
    activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }


class SignupRequest(BaseModel):
    email: EmailStr


def validate_activity_name(name: str) -> None:
    """Basic validation to reduce risk of injection via unexpected path values.

    Allowed characters: letters, numbers, spaces, hyphens, underscores, apostrophes.
    Length: 1..100
    """
    if not (1 <= len(name) <= 100):
        raise HTTPException(status_code=400, detail="Invalid activity name length")

    if not re.match(r"^[\w\s\-']+$", name):
        raise HTTPException(status_code=400, detail="Activity name contains invalid characters")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, payload: SignupRequest = Body(None), email: str = None):
    """Sign up a student for an activity.

    Accepts email in the JSON body (preferred) or as a query parameter for backwards compatibility.
    """
    validate_activity_name(activity_name)

    # Support both body and query param for email (body preferred)
    user_email = None
    if payload is not None and getattr(payload, "email", None):
        user_email = payload.email
    elif email:
        user_email = email

    if not user_email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    participants = activity.setdefault("participants", [])

    # Validate student is not already signed up
    if user_email in participants:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    participants.append(user_email)
    return {"message": f"Signed up {user_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    validate_activity_name(activity_name)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    participants = activity.get("participants", [])

    # Validate student is signed up
    if email not in participants:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    participants.remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
