"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json
from pathlib import Path
from typing import Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import logging
security = HTTPBasic()

# Load teacher credentials from JSON file
def load_teachers():
    with open(os.path.join(Path(__file__).parent, "teachers.json")) as f:
        data = json.load(f)
    return {t["username"]: t["password"] for t in data["teachers"]}

TEACHERS = load_teachers()

# Set up logging for certificate access
logging.basicConfig(filename=os.path.join(Path(__file__).parent, "certificate_access.log"),
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Directory to store uploaded certificates
CERT_DIR = os.path.join(Path(__file__).parent, "certificates")
os.makedirs(CERT_DIR, exist_ok=True)

# Auth dependency
def teacher_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = TEACHERS.get(credentials.username)
    if not correct_password or not secrets.compare_digest(credentials.password, correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Endpoint: Upload certificate (teachers only)
@app.post("/certificates/upload")
def upload_certificate(
    activity_name: str = Form(...),
    participant_email: str = Form(...),
    file: UploadFile = File(...),
    username: str = Depends(teacher_auth)
):
    # Save file as <activity>_<email>_<filename>
    safe_email = participant_email.replace("@", "_at_").replace(".", "_")
    cert_filename = f"{activity_name}_{safe_email}_{file.filename}"
    cert_path = os.path.join(CERT_DIR, cert_filename)
    with open(cert_path, "wb") as f_out:
        f_out.write(file.file.read())
    logging.info(f"Certificate uploaded: {cert_filename} by {username}")
    return {"message": "Certificate uploaded successfully."}

# Endpoint: Download certificate (teachers only)
@app.get("/certificates/download")
def download_certificate(
    activity_name: str,
    participant_email: str,
    filename: str,
    username: str = Depends(teacher_auth)
):
    safe_email = participant_email.replace("@", "_at_").replace(".", "_")
    cert_filename = f"{activity_name}_{safe_email}_{filename}"
    cert_path = os.path.join(CERT_DIR, cert_filename)
    if not os.path.exists(cert_path):
        raise HTTPException(status_code=404, detail="Certificate not found")
    logging.info(f"Certificate accessed: {cert_filename} by {username}")
    from fastapi.responses import FileResponse
    return FileResponse(cert_path, filename=filename)

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
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
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
