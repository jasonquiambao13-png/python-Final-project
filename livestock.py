# livestock.py
# Defines the Livestock class (one animal record) using OOP.

from datetime import datetime


class Livestock:
    """Represents one livestock animal."""

    # Allowed values (also used for the dropdowns in the forms)
    TYPES = ["Cattle", "Pig", "Goat", "Chicken", "Other"]
    SEXES = ["Male", "Female"]
    HEALTH_STATUSES = ["Healthy", "Sick", "Under Treatment", "Recovering"]

    def __init__(self, id_number, name, type, breed, sex, birth_date,
                 weight, health_status, date_acquired, livestock_id=None):
        self.livestock_id = livestock_id      # set by MySQL (AUTO_INCREMENT)
        self.id_number = id_number
        self.name = name
        self.type = type
        self.breed = breed
        self.sex = sex
        self.birth_date = birth_date          # text in YYYY-MM-DD format
        self.weight = weight
        self.health_status = health_status
        self.date_acquired = date_acquired    # text in YYYY-MM-DD format

    def validate(self):
        """Check the data. Returns an error message, or "" if everything is OK."""
        # Clean up extra spaces
        self.id_number = str(self.id_number).strip()
        self.name = str(self.name).strip()
        self.breed = str(self.breed).strip()

        if self.id_number == "":
            return "Identification number is required."
        if self.name == "":
            return "Name is required."
        if self.type not in Livestock.TYPES:
            return "Please select a valid livestock type."
        if self.sex not in Livestock.SEXES:
            return "Please select a valid sex."
        if self.health_status not in Livestock.HEALTH_STATUSES:
            return "Please select a valid health status."

        # Weight must be a number that is not negative
        try:
            self.weight = float(self.weight) if str(self.weight).strip() != "" else 0.0
        except ValueError:
            return "Weight must be a number."
        if self.weight < 0:
            return "Weight cannot be negative."

        # Dates are optional, but must be YYYY-MM-DD if filled in
        if not self._is_valid_date(self.birth_date):
            return "Birth date must be in YYYY-MM-DD format."
        if not self._is_valid_date(self.date_acquired):
            return "Date acquired must be in YYYY-MM-DD format."

        return ""

    def _is_valid_date(self, date_text):
        """Return True if the date is empty or in YYYY-MM-DD format."""
        if str(date_text).strip() == "":
            return True
        try:
            datetime.strptime(str(date_text).strip(), "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def to_tuple(self):
        """Return the values in the same order as the livestock table columns
        (without livestock_id). Empty dates become None (NULL in MySQL)."""
        birth = str(self.birth_date).strip() or None
        acquired = str(self.date_acquired).strip() or None
        return (self.id_number, self.name, self.type, self.breed, self.sex,
                birth, self.weight, self.health_status, acquired)

    def __str__(self):
        return f"{self.id_number} - {self.name} ({self.type})"
