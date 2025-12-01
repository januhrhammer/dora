"""
Main FastAPI application for the medicine tracking system.

This is the entry point of the backend API. It defines all the HTTP endpoints
for managing drugs and sets up scheduled email reminders.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file (for local development)
# In production/Docker, environment variables are set via docker-compose
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from . import models, schemas, crud
from .database import engine, get_db
from .email_service import email_service
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
    LoginRequest,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Database tables are managed by Alembic migrations
# To apply migrations, run: alembic upgrade head
# To create a new migration after model changes: alembic revision --autogenerate -m "description"

# Initialize FastAPI app
app = FastAPI(
    title="Medicine Tracker API",
    description="API for tracking grandma's medicine and sending reminders",
    version="1.0.0",
)

# CORS middleware to allow frontend to communicate with backend
# In production, replace "*" with your specific frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scheduler for automated reminders
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    """
    Run when the application starts.

    Sets up scheduled tasks for automatic email reminders:
    - Weekly reminder: Every Sunday at 9:00 AM
    - Reorder check: Every day at 10:00 AM
    """
    # Weekly reminder every Sunday at 9:00 AM
    scheduler.add_job(
        send_weekly_reminder_job,
        CronTrigger(day_of_week="sun", hour=9, minute=0),
        id="weekly_reminder",
    )

    # Daily check for reorder needs at 10:00 AM
    scheduler.add_job(
        send_reorder_reminder_job,
        CronTrigger(hour=10, minute=0),
        id="reorder_reminder",
    )

    scheduler.start()
    print("Scheduler started. Reminders will be sent automatically.")


@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    scheduler.shutdown()


async def send_weekly_reminder_job():
    """Background job to send weekly medicine setup reminder."""
    db = next(get_db())
    try:
        drugs = crud.get_drugs(db)
        await email_service.send_weekly_reminder(drugs)
    finally:
        db.close()


async def send_reorder_reminder_job():
    """Background job to check and send reorder reminders."""
    db = next(get_db())
    try:
        all_drugs = crud.get_drugs(db)
        drugs_to_reorder = crud.get_drugs_needing_reorder(db)
        doctor_vacation = crud.get_current_doctor_vacation(db)
        if drugs_to_reorder:
            await email_service.send_reorder_reminder(drugs_to_reorder, all_drugs, doctor_vacation)
    finally:
        db.close()


# ============================================================================
# API ROUTES
# ============================================================================


@app.get("/")
async def root():
    """
    Root endpoint - health check.

    Returns:
        dict: Welcome message.
    """
    return {"message": "Medicine Tracker API is running"}


@app.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login endpoint for authentication.

    Args:
        login_data (LoginRequest): Username and password.

    Returns:
        Token: JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    if not authenticate_user(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": login_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/drugs/", response_model=schemas.DrugResponse, status_code=201)
async def create_drug(
    drug: schemas.DrugCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Create a new drug in the system.

    Args:
        drug (DrugCreate): Drug information.
        db (Session): Database session (injected).

    Returns:
        DrugResponse: The created drug with all fields.
    """
    return crud.create_drug(db, drug)


@app.get("/drugs/", response_model=List[schemas.DrugResponse])
async def get_drugs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get all drugs.

    Args:
        skip (int): Number of records to skip (pagination).
        limit (int): Max number of records to return.
        db (Session): Database session (injected).

    Returns:
        List[DrugResponse]: List of all drugs.
    """
    return crud.get_drugs(db, skip=skip, limit=limit)


@app.get("/drugs/{drug_id}", response_model=schemas.DrugResponse)
async def get_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get a specific drug by ID.

    Args:
        drug_id (int): The drug's ID.
        db (Session): Database session (injected).

    Returns:
        DrugResponse: The drug information.

    Raises:
        HTTPException: 404 if drug not found.
    """
    drug = crud.get_drug(db, drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug


@app.put("/drugs/{drug_id}", response_model=schemas.DrugResponse)
async def update_drug(
    drug_id: int,
    drug_update: schemas.DrugUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Update a drug's information.

    Args:
        drug_id (int): The drug's ID.
        drug_update (DrugUpdate): Fields to update.
        db (Session): Database session (injected).

    Returns:
        DrugResponse: The updated drug.

    Raises:
        HTTPException: 404 if drug not found.
    """
    drug = crud.update_drug(db, drug_id, drug_update)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug


@app.delete("/drugs/{drug_id}", status_code=204)
async def delete_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a drug from the system.

    Args:
        drug_id (int): The drug's ID.
        db (Session): Database session (injected).

    Returns:
        None: 204 No Content on success.

    Raises:
        HTTPException: 404 if drug not found.
    """
    success = crud.delete_drug(db, drug_id)
    if not success:
        raise HTTPException(status_code=404, detail="Drug not found")
    return None


@app.post("/drugs/{drug_id}/refill", response_model=schemas.DrugResponse)
async def refill_drug(
    drug_id: int,
    refill: schemas.DrugRefill,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Refill a drug (add packages).

    Args:
        drug_id (int): The drug's ID.
        refill (DrugRefill): Number of packages to add.
        db (Session): Database session (injected).

    Returns:
        DrugResponse: The updated drug with new pill count.

    Raises:
        HTTPException: 404 if drug not found.
    """
    drug = crud.refill_drug(db, drug_id, refill.packages)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug


@app.get("/drugs-status/reorder", response_model=List[schemas.DrugResponse])
async def get_drugs_needing_reorder(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get drugs that need reordering (< 3 weeks remaining).

    Args:
        db (Session): Database session (injected).

    Returns:
        List[DrugResponse]: Drugs needing reorder.
    """
    return crud.get_drugs_needing_reorder(db)


@app.post("/test-email")
async def send_test_email(current_user: str = Depends(get_current_user)):
    """
    Send a test email to verify email configuration.

    Returns:
        dict: Success or error message.
    """
    success = await email_service.send_test_email()
    if success:
        return {"message": "Test email sent successfully"}
    else:
        return {"message": "Failed to send test email. Check configuration."}


@app.post("/send-weekly-reminder")
async def trigger_weekly_reminder(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Manually trigger the weekly reminder email.

    Useful for testing without waiting for the scheduled time.

    Args:
        db (Session): Database session (injected).

    Returns:
        dict: Success or error message.
    """
    drugs = crud.get_drugs(db)
    success = await email_service.send_weekly_reminder(drugs)
    if success:
        return {"message": "Weekly reminder sent successfully"}
    else:
        return {"message": "Failed to send reminder"}


@app.post("/send-reorder-reminder")
async def trigger_reorder_reminder(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Manually trigger the reorder reminder email.

    Useful for testing without waiting for the scheduled time.

    Args:
        db (Session): Database session (injected).

    Returns:
        dict: Success or error message.
    """
    all_drugs = crud.get_drugs(db)
    drugs_to_reorder = crud.get_drugs_needing_reorder(db)
    doctor_vacation = crud.get_current_doctor_vacation(db)
    if not drugs_to_reorder:
        return {"message": "No drugs need reordering at this time"}

    success = await email_service.send_reorder_reminder(drugs_to_reorder, all_drugs, doctor_vacation)
    if success:
        return {"message": f"Reorder reminder sent for {len(drugs_to_reorder)} drug(s)"}
    else:
        return {"message": "Failed to send reminder"}


# ============================================================================
# DOCTOR VACATION ROUTES
# ============================================================================


@app.post("/doctor-vacations/", response_model=schemas.DoctorVacationResponse)
def create_doctor_vacation(
    vacation: schemas.DoctorVacationCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Create a new doctor vacation period.

    Args:
        vacation (DoctorVacationCreate): Vacation data.
        db (Session): Database session (injected).

    Returns:
        DoctorVacationResponse: The created vacation period.
    """
    return crud.create_doctor_vacation(db, vacation)


@app.get("/doctor-vacations/", response_model=List[schemas.DoctorVacationResponse])
def get_doctor_vacations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get all doctor vacation periods.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        db (Session): Database session (injected).

    Returns:
        List[DoctorVacationResponse]: List of vacation periods.
    """
    return crud.get_doctor_vacations(db, skip=skip, limit=limit)


@app.get("/doctor-vacations/current", response_model=schemas.DoctorVacationResponse | None)
def get_current_doctor_vacation(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get the current doctor vacation (if doctor is on vacation today).

    Args:
        db (Session): Database session (injected).

    Returns:
        DoctorVacationResponse or None: Current vacation if applicable.
    """
    return crud.get_current_doctor_vacation(db)


@app.get("/doctor-vacations/{vacation_id}", response_model=schemas.DoctorVacationResponse)
def get_doctor_vacation(
    vacation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get a specific doctor vacation period.

    Args:
        vacation_id (int): The vacation ID.
        db (Session): Database session (injected).

    Returns:
        DoctorVacationResponse: The vacation period.

    Raises:
        HTTPException: 404 if vacation not found.
    """
    db_vacation = crud.get_doctor_vacation(db, vacation_id)
    if not db_vacation:
        raise HTTPException(status_code=404, detail="Doctor vacation not found")
    return db_vacation


@app.put("/doctor-vacations/{vacation_id}", response_model=schemas.DoctorVacationResponse)
def update_doctor_vacation(
    vacation_id: int,
    vacation: schemas.DoctorVacationUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Update a doctor vacation period.

    Args:
        vacation_id (int): The vacation ID.
        vacation (DoctorVacationUpdate): Fields to update.
        db (Session): Database session (injected).

    Returns:
        DoctorVacationResponse: The updated vacation period.

    Raises:
        HTTPException: 404 if vacation not found.
    """
    db_vacation = crud.update_doctor_vacation(db, vacation_id, vacation)
    if not db_vacation:
        raise HTTPException(status_code=404, detail="Doctor vacation not found")
    return db_vacation


@app.delete("/doctor-vacations/{vacation_id}")
def delete_doctor_vacation(
    vacation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a doctor vacation period.

    Args:
        vacation_id (int): The vacation ID.
        db (Session): Database session (injected).

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 404 if vacation not found.
    """
    success = crud.delete_doctor_vacation(db, vacation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Doctor vacation not found")
    return {"message": "Doctor vacation deleted successfully"}
