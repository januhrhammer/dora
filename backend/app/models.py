"""
Database models for the medicine tracking application.

This module defines the SQLAlchemy ORM models for storing drug information
and doctor vacation periods.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Date
from datetime import datetime, date
from .database import Base


class Drug(Base):
    """
    Drug model representing a medicine in grandma's medicine plan.

    Attributes:
        id (int): Primary key, auto-incrementing identifier.
        name (str): Name of the drug/medicine.
        dosage_strength (str): Dosage strength (e.g., "75µg", "100mg", "5ml").
        package_size (int): Number of pills per package.
        schedule_type (str): Type of schedule - "daily", "weekly_alternating".
        morning_pre_food (float): Pills to take in the morning before food (0 if not taken).
        morning_post_food (float): Pills to take in the morning after food (0 if not taken).
        evening_pre_food (float): Pills to take in the evening before food (0 if not taken).
        evening_post_food (float): Pills to take in the evening after food (0 if not taken).
        even_week_pills (float): Total pills per week in even weeks (for weekly_alternating).
        odd_week_pills (float): Total pills per week in odd weeks (for weekly_alternating).
        current_amount (float): Current number of pills remaining (supports half pills).
        notes (str): Optional notes (e.g., specific instructions).
        last_refilled_at (datetime): When this drug was last refilled (None if never refilled).
        created_at (datetime): When this drug was added to the system.
        updated_at (datetime): When this drug was last modified.

    Examples:
        Moxonidin (daily): 2 pills morning after food, 1 pill evening after food:
        schedule_type="daily", morning_pre_food=0, morning_post_food=2,
        evening_pre_food=0, evening_post_food=1

        L-thyroxin 75µg (weekly alternating): 4 pills in even weeks, 3 in odd weeks:
        schedule_type="weekly_alternating", dosage_strength="75µg",
        morning_pre_food=1, even_week_pills=4, odd_week_pills=3
    """

    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    dosage_strength = Column(String, nullable=True)  # e.g., "75µg", "100mg"
    package_size = Column(Integer, nullable=False)  # pills per package
    schedule_type = Column(String, nullable=False, default="daily")  # "daily" or "weekly_alternating"
    morning_pre_food = Column(Float, nullable=False, default=0)
    morning_post_food = Column(Float, nullable=False, default=0)
    evening_pre_food = Column(Float, nullable=False, default=0)
    evening_post_food = Column(Float, nullable=False, default=0)
    even_week_pills = Column(Float, nullable=True)  # for weekly_alternating schedule
    odd_week_pills = Column(Float, nullable=True)  # for weekly_alternating schedule
    current_amount = Column(Float, nullable=False, default=0)
    notes = Column(String, nullable=True)
    last_refilled_at = Column(DateTime, nullable=True)  # Tracks when drug was last refilled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def daily_consumption(self) -> float:
        """
        Calculate how many pills are consumed per day.

        Returns:
            float: Average pills consumed daily.

        For daily schedules: sum of all doses per day.
        For weekly alternating: average of (even_week + odd_week) / 14 days.
        """
        if self.schedule_type == "weekly_alternating":
            # Average consumption over a 2-week cycle
            if self.even_week_pills is not None and self.odd_week_pills is not None:
                return (self.even_week_pills + self.odd_week_pills) / 14.0
            return 0
        else:
            # Daily schedule: sum of all doses
            return (self.morning_pre_food + self.morning_post_food +
                    self.evening_pre_food + self.evening_post_food)

    @property
    def days_remaining(self) -> float:
        """
        Calculate how many days worth of pills remain.

        Returns:
            float: Number of days until pills run out. Returns 0 if none remain.
        """
        if self.daily_consumption == 0:
            return 0
        return self.current_amount / self.daily_consumption

    @property
    def weeks_remaining(self) -> float:
        """
        Calculate how many weeks worth of pills remain.

        Returns:
            float: Number of weeks until pills run out.
        """
        return self.days_remaining / 7

    @property
    def needs_reorder(self) -> bool:
        """
        Check if drug needs to be reordered (less than 3 weeks remaining).

        Returns:
            bool: True if less than 3 weeks of pills remain, False otherwise.
        """
        return self.weeks_remaining < 3

    @property
    def current_week_type(self) -> str:
        """
        Determine if current week is even or odd.

        Returns:
            str: "even" or "odd" based on ISO week number.
        """
        from datetime import datetime
        week_number = datetime.now().isocalendar()[1]
        return "even" if week_number % 2 == 0 else "odd"

    @property
    def current_week_pills(self) -> float:
        """
        Get pills for current week (for weekly_alternating schedule).

        Returns:
            float: Pills for this week, or 0 if not applicable.
        """
        if self.schedule_type == "weekly_alternating":
            if self.current_week_type == "even":
                return self.even_week_pills or 0
            else:
                return self.odd_week_pills or 0
        return 0


class DoctorVacation(Base):
    """
    DoctorVacation model representing a period when the doctor is unavailable.

    Used to warn when trying to order medications during doctor's vacation,
    especially important for quarterly insurance card requirements.

    Attributes:
        id (int): Primary key, auto-incrementing identifier.
        start_date (date): First day of vacation.
        end_date (date): Last day of vacation.
        notes (str): Optional notes (e.g., "Summer vacation", "Conference").
        created_at (datetime): When this vacation period was added.
        updated_at (datetime): When this vacation period was last modified.

    Examples:
        Doctor vacation from Dec 24 to Jan 1:
        start_date=date(2024, 12, 24), end_date=date(2025, 1, 1)
    """

    __tablename__ = "doctor_vacations"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_current(self) -> bool:
        """
        Check if the vacation period includes today.

        Returns:
            bool: True if today falls within the vacation period.
        """
        today = date.today()
        return self.start_date <= today <= self.end_date

    @property
    def is_upcoming(self) -> bool:
        """
        Check if the vacation period is in the future.

        Returns:
            bool: True if vacation starts in the future.
        """
        return date.today() < self.start_date

    @property
    def is_past(self) -> bool:
        """
        Check if the vacation period has ended.

        Returns:
            bool: True if vacation has ended.
        """
        return date.today() > self.end_date
