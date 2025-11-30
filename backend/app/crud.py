"""
CRUD (Create, Read, Update, Delete) operations for the database.

This module contains all the database operations for managing drugs.
It separates database logic from the API routes for better organization.
"""

from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional
from datetime import datetime, date


def create_drug(db: Session, drug: schemas.DrugCreate) -> models.Drug:
    """
    Create a new drug in the database.

    Args:
        db (Session): Database session.
        drug (DrugCreate): Drug data from the request.

    Returns:
        Drug: The newly created drug object with ID assigned.
    """
    db_drug = models.Drug(**drug.model_dump())
    db.add(db_drug)
    db.commit()
    db.refresh(db_drug)
    return db_drug


def get_drug(db: Session, drug_id: int) -> Optional[models.Drug]:
    """
    Get a single drug by its ID.

    Args:
        db (Session): Database session.
        drug_id (int): The drug's ID.

    Returns:
        Drug or None: The drug if found, None otherwise.
    """
    return db.query(models.Drug).filter(models.Drug.id == drug_id).first()


def get_drugs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Drug]:
    """
    Get a list of all drugs with pagination.

    Args:
        db (Session): Database session.
        skip (int): Number of records to skip (for pagination).
        limit (int): Maximum number of records to return.

    Returns:
        List[Drug]: List of drug objects.
    """
    return db.query(models.Drug).offset(skip).limit(limit).all()


def update_drug(
    db: Session, drug_id: int, drug_update: schemas.DrugUpdate
) -> Optional[models.Drug]:
    """
    Update an existing drug.

    Args:
        db (Session): Database session.
        drug_id (int): The drug's ID.
        drug_update (DrugUpdate): Fields to update.

    Returns:
        Drug or None: The updated drug if found, None otherwise.

    Only fields provided in drug_update will be changed.
    """
    db_drug = get_drug(db, drug_id)
    if not db_drug:
        return None

    # Update only provided fields
    update_data = drug_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_drug, field, value)

    db.commit()
    db.refresh(db_drug)
    return db_drug


def delete_drug(db: Session, drug_id: int) -> bool:
    """
    Delete a drug from the database.

    Args:
        db (Session): Database session.
        drug_id (int): The drug's ID.

    Returns:
        bool: True if deleted, False if not found.
    """
    db_drug = get_drug(db, drug_id)
    if not db_drug:
        return False

    db.delete(db_drug)
    db.commit()
    return True


def refill_drug(db: Session, drug_id: int, packages: int) -> Optional[models.Drug]:
    """
    Add pills to a drug's current amount (refill).

    Args:
        db (Session): Database session.
        drug_id (int): The drug's ID.
        packages (int): Number of packages to add.

    Returns:
        Drug or None: The updated drug if found, None otherwise.

    This calculates pills_to_add = packages * package_size and adds them
    to the current_amount. Also updates last_refilled_at to track when
    the drug was refilled for quarterly insurance card reminders.
    """
    db_drug = get_drug(db, drug_id)
    if not db_drug:
        return None

    pills_to_add = packages * db_drug.package_size
    db_drug.current_amount += pills_to_add
    db_drug.last_refilled_at = datetime.utcnow()

    db.commit()
    db.refresh(db_drug)
    return db_drug


def get_drugs_needing_reorder(db: Session) -> List[models.Drug]:
    """
    Get all drugs that need to be reordered (< 3 weeks remaining).

    Args:
        db (Session): Database session.

    Returns:
        List[Drug]: Drugs that need reordering.

    This queries all drugs and filters those with less than 3 weeks remaining.
    """
    all_drugs = get_drugs(db)
    return [drug for drug in all_drugs if drug.needs_reorder]


# Doctor Vacation CRUD operations

def create_doctor_vacation(db: Session, vacation: schemas.DoctorVacationCreate) -> models.DoctorVacation:
    """
    Create a new doctor vacation period.

    Args:
        db (Session): Database session.
        vacation (DoctorVacationCreate): Vacation data.

    Returns:
        DoctorVacation: The created vacation period.
    """
    db_vacation = models.DoctorVacation(**vacation.model_dump())
    db.add(db_vacation)
    db.commit()
    db.refresh(db_vacation)
    return db_vacation


def get_doctor_vacation(db: Session, vacation_id: int) -> Optional[models.DoctorVacation]:
    """
    Get a specific doctor vacation period by ID.

    Args:
        db (Session): Database session.
        vacation_id (int): The vacation period's ID.

    Returns:
        DoctorVacation or None: The vacation if found, None otherwise.
    """
    return db.query(models.DoctorVacation).filter(models.DoctorVacation.id == vacation_id).first()


def get_doctor_vacations(db: Session, skip: int = 0, limit: int = 100) -> List[models.DoctorVacation]:
    """
    Get all doctor vacation periods.

    Args:
        db (Session): Database session.
        skip (int): Number of records to skip (for pagination).
        limit (int): Maximum number of records to return.

    Returns:
        List[DoctorVacation]: List of vacation periods, ordered by start_date.
    """
    return db.query(models.DoctorVacation).order_by(models.DoctorVacation.start_date).offset(skip).limit(limit).all()


def update_doctor_vacation(db: Session, vacation_id: int, vacation_update: schemas.DoctorVacationUpdate) -> Optional[models.DoctorVacation]:
    """
    Update a doctor vacation period.

    Args:
        db (Session): Database session.
        vacation_id (int): The vacation period's ID.
        vacation_update (DoctorVacationUpdate): Fields to update.

    Returns:
        DoctorVacation or None: The updated vacation if found, None otherwise.
    """
    db_vacation = get_doctor_vacation(db, vacation_id)
    if not db_vacation:
        return None

    update_data = vacation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vacation, field, value)

    db.commit()
    db.refresh(db_vacation)
    return db_vacation


def delete_doctor_vacation(db: Session, vacation_id: int) -> bool:
    """
    Delete a doctor vacation period.

    Args:
        db (Session): Database session.
        vacation_id (int): The vacation period's ID.

    Returns:
        bool: True if deleted, False if not found.
    """
    db_vacation = get_doctor_vacation(db, vacation_id)
    if not db_vacation:
        return False

    db.delete(db_vacation)
    db.commit()
    return True


def get_current_doctor_vacation(db: Session) -> Optional[models.DoctorVacation]:
    """
    Get the current doctor vacation period (if doctor is on vacation today).

    Args:
        db (Session): Database session.

    Returns:
        DoctorVacation or None: Current vacation if doctor is on vacation, None otherwise.
    """
    today = date.today()
    return db.query(models.DoctorVacation).filter(
        models.DoctorVacation.start_date <= today,
        models.DoctorVacation.end_date >= today
    ).first()
