"""
Email service for sending reminders using Mailjet.

This module handles sending email notifications for:
- Weekly medicine setup reminders
- Reorder reminders when pills are running low
- Quarterly insurance card reminders

Uses Mailjet API for reliable transactional email delivery.
"""

from mailjet_rest import Client
from typing import List, Optional
from . import models
import os
from datetime import datetime


class EmailService:
    """
    Service for sending email reminders using Mailjet.

    Attributes:
        api_key (str): Mailjet API key.
        api_secret (str): Mailjet API secret.
        from_email (str): Email address to send from (must be verified in Mailjet).
        from_name (str): Name to display as sender.
        to_email (str): Email address to send to (grandma or caretaker).
        to_name (str): Name of the recipient.
    """

    def __init__(self):
        """Initialize email service with Mailjet configuration from environment variables."""
        self.api_key = os.getenv("MAILJET_API_KEY", "")
        self.api_secret = os.getenv("MAILJET_API_SECRET", "")
        self.from_email = os.getenv("FROM_EMAIL", "")
        self.from_name = os.getenv("FROM_NAME", "Medicine Tracker")
        self.to_email = os.getenv("TO_EMAIL", "")
        self.to_name = os.getenv("TO_NAME", "")

        # Initialize Mailjet client
        if self.api_key and self.api_secret:
            self.mailjet = Client(auth=(self.api_key, self.api_secret), version='v3.1')
        else:
            self.mailjet = None

    async def send_email(self, subject: str, body: str) -> bool:
        """
        Send an email using Mailjet API.

        Args:
            subject (str): Email subject line.
            body (str): Email body content (plain text).

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.mailjet or not self.from_email or not self.to_email:
            print("Mailjet not configured. Skipping email send.")
            print("Required: MAILJET_API_KEY, MAILJET_API_SECRET, FROM_EMAIL, TO_EMAIL")
            return False

        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": self.to_email,
                                "Name": self.to_name or self.to_email
                            }
                        ],
                        "Subject": subject,
                        "TextPart": body,
                    }
                ]
            }

            result = self.mailjet.send.create(data=data)

            if result.status_code == 200:
                print(f"Email sent successfully: {subject}")
                return True
            else:
                print(f"Failed to send email. Status: {result.status_code}")
                print(f"Response: {result.json()}")
                return False

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_weekly_reminder(self, drugs: List[models.Drug]) -> bool:
        """
        Send weekly reminder to set up medicines for the week.

        Args:
            drugs (List[Drug]): List of all drugs in the system.

        Returns:
            bool: True if sent successfully.
        """
        subject = "Weekly Medicine Reminder - Time to Set Up Pills"

        body = "Hello! It's time to set up grandma's medicines for the week.\n\n"
        body += "Current Medicine Plan:\n"
        body += "-" * 50 + "\n\n"

        for drug in drugs:
            body += f"• {drug.name}"
            if drug.dosage_strength:
                body += f" ({drug.dosage_strength})"
            body += "\n"

            # Show schedule based on type
            if drug.schedule_type == 'weekly_alternating':
                body += f"  Schedule: Weekly alternating ({drug.current_week_type} week)\n"
                body += f"  This week: {drug.current_week_pills} pills\n"
            else:
                total_daily = drug.morning_pre_food + drug.morning_post_food + drug.evening_pre_food + drug.evening_post_food
                body += f"  Daily: {total_daily} pill(s)\n"

            body += f"  Pills remaining: {drug.current_amount}\n"
            body += f"  Days remaining: {drug.days_remaining:.1f} days\n\n"

        body += "\nHave a great week!\n"

        return await self.send_email(subject, body)

    async def send_reorder_reminder(self, drugs: List[models.Drug], all_drugs: List[models.Drug], doctor_vacation: Optional[models.DoctorVacation] = None) -> bool:
        """
        Send reminder to reorder medicines that are running low.

        Args:
            drugs (List[Drug]): List of drugs that need reordering.
            all_drugs (List[Drug]): List of all drugs (to check quarterly refills).
            doctor_vacation (DoctorVacation, optional): Current doctor vacation if applicable.

        Returns:
            bool: True if sent successfully.
        """
        if not drugs:
            return False

        subject = "Medikamentenbestellung - Dora Langenhop"

        body = "Guten Tag,\n\n"
        body += "es werden Rezepte benötigt für die folgenden Medikamente für Dora Langenhop, geb. 23.04.1937.\n\n"

        for drug in drugs:
            body += f"- {drug.name}"
            if drug.dosage_strength:
                body += f" {drug.dosage_strength}"
            body += f", Packungsgröße: {drug.package_size} Tabletten\n"


        body += "\nViele Grüße\n"
        body += "Jan Uhrhammer"

        return await self.send_email(subject, body)

    def _is_first_order_of_quarter(self, all_drugs: List[models.Drug]) -> bool:
        """
        Check if this is the first order of the current quarter.

        Args:
            all_drugs (List[Drug]): List of all drugs.

        Returns:
            bool: True if no drug was refilled in the current quarter.
        """
        now = datetime.now()
        current_year = now.year
        current_quarter = (now.month - 1) // 3 + 1  # 1, 2, 3, or 4

        # Calculate the start month of the current quarter
        quarter_start_month = (current_quarter - 1) * 3 + 1

        # Check if any drug was refilled in the current quarter
        for drug in all_drugs:
            if drug.last_refilled_at:
                refill_year = drug.last_refilled_at.year
                refill_month = drug.last_refilled_at.month
                refill_quarter = (refill_month - 1) // 3 + 1

                # If refilled in current quarter and year, it's not the first order
                if refill_year == current_year and refill_quarter == current_quarter:
                    return False

        # No drug was refilled this quarter, so this is the first order
        return True

    async def send_test_email(self) -> bool:
        """
        Send a test email to verify Mailjet configuration.

        Returns:
            bool: True if sent successfully.
        """
        subject = "Medicine Tracker - Test Email"
        body = "This is a test email from your medicine tracking system.\n\n"
        body += "Mailjet integration is working correctly!\n\n"
        body += "Your automated reminders will be sent reliably using Mailjet."
        return await self.send_email(subject, body)


# Global email service instance
email_service = EmailService()
