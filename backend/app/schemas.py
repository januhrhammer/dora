"""
Pydantic schemas for request/response validation.

These schemas define the shape of data coming into and out of the API.
They provide automatic validation and documentation for the FastAPI endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional


class DrugBase(BaseModel):
    """
    Base schema with common drug fields.

    This is inherited by other schemas to avoid duplication.
    """

    name: str = Field(..., description="Name of the medicine")
    dosage_strength: Optional[str] = Field(None, description="Dosage strength (e.g., '75µg', '100mg')")
    package_size: int = Field(..., gt=0, description="Number of pills per package")
    schedule_type: str = Field("daily", description="Schedule type: 'daily' or 'weekly_alternating'")
    morning_pre_food: float = Field(0, ge=0, description="Pills in morning before food")
    morning_post_food: float = Field(0, ge=0, description="Pills in morning after food")
    evening_pre_food: float = Field(0, ge=0, description="Pills in evening before food")
    evening_post_food: float = Field(0, ge=0, description="Pills in evening after food")
    even_week_pills: Optional[float] = Field(None, ge=0, description="Pills per week in even weeks (weekly_alternating)")
    odd_week_pills: Optional[float] = Field(None, ge=0, description="Pills per week in odd weeks (weekly_alternating)")
    current_amount: float = Field(0, ge=0, description="Current number of pills remaining")
    notes: Optional[str] = Field(None, description="Optional notes or instructions")


class DrugCreate(DrugBase):
    """
    Schema for creating a new drug.

    Inherits all fields from DrugBase. Used when POST /drugs is called.
    """

    pass


class DrugUpdate(BaseModel):
    """
    Schema for updating an existing drug.

    All fields are optional to allow partial updates.
    Only provided fields will be updated.
    """

    name: Optional[str] = None
    dosage_strength: Optional[str] = None
    package_size: Optional[int] = Field(None, gt=0)
    schedule_type: Optional[str] = None
    morning_pre_food: Optional[float] = Field(None, ge=0)
    morning_post_food: Optional[float] = Field(None, ge=0)
    evening_pre_food: Optional[float] = Field(None, ge=0)
    evening_post_food: Optional[float] = Field(None, ge=0)
    even_week_pills: Optional[float] = Field(None, ge=0)
    odd_week_pills: Optional[float] = Field(None, ge=0)
    current_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class DrugResponse(DrugBase):
    """
    Schema for drug responses.

    Includes additional computed fields and database metadata.
    This is what the API returns when you query drug information.
    """

    id: int
    daily_consumption: float = Field(..., description="Pills consumed per day")
    days_remaining: float = Field(..., description="Days until pills run out")
    weeks_remaining: float = Field(..., description="Weeks until pills run out")
    needs_reorder: bool = Field(..., description="True if < 3 weeks remaining")
    current_week_type: str = Field(..., description="Current week type: 'even' or 'odd'")
    current_week_pills: float = Field(..., description="Pills for this week (weekly_alternating only)")
    last_refilled_at: Optional[datetime] = Field(None, description="When drug was last refilled")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Allows creating from ORM models


class DrugRefill(BaseModel):
    """
    Schema for refilling a drug's pill count.

    Used when you receive a new package and want to add pills to the current amount.
    """

    packages: int = Field(..., gt=0, description="Number of packages to add")


class DoctorVacationBase(BaseModel):
    """
    Base schema for doctor vacation periods.

    Used to track when the doctor is unavailable.
    """

    start_date: date = Field(..., description="First day of vacation")
    end_date: date = Field(..., description="Last day of vacation")
    notes: Optional[str] = Field(None, description="Optional notes about the vacation")


class DoctorVacationCreate(DoctorVacationBase):
    """
    Schema for creating a new doctor vacation period.

    Inherits all fields from DoctorVacationBase.
    """

    pass


class DoctorVacationUpdate(BaseModel):
    """
    Schema for updating a doctor vacation period.

    All fields are optional to allow partial updates.
    """

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class DoctorVacationResponse(DoctorVacationBase):
    """
    Schema for doctor vacation responses.

    Includes database metadata and computed properties.
    """

    id: int
    is_current: bool = Field(..., description="True if vacation includes today")
    is_upcoming: bool = Field(..., description="True if vacation is in the future")
    is_past: bool = Field(..., description="True if vacation has ended")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Allows creating from ORM models
