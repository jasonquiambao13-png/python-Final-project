# livestock_manager.py
# Handles all database logic: CRUD, searching, filtering, and dashboard summaries
# for livestock, health records, breeding records, and expenses.
# Methods raise ValueError for invalid input. The GUI shows the message.

from datetime import datetime

from database import Database
from livestock import Livestock


def is_valid_date(date_text, required=False):
    """Return True if date_text is in YYYY-MM-DD format.
    An empty date is OK unless required=True."""
    date_text = str(date_text).strip()
    if date_text == "":
        return not required
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def clean_row(row):
    """Convert a database row to a tuple of text (None becomes empty text)
    so it can be shown in a Treeview or placed in an entry field."""
    return tuple("" if value is None else str(value) for value in row)


class LivestockManager:
    """Connects to the database and performs all operations."""

    BREEDING_STATUSES = ["Bred", "Pregnant", "Delivered", "Failed"]
    EXPENSE_CATEGORIES = ["Feed", "Medicine", "Vaccination", "Other"]

    # Column order used by every livestock SELECT query
    LIVESTOCK_COLUMNS = ("livestock_id, id_number, name, type, breed, sex, "
                         "birth_date, weight, health_status, date_acquired")

    def __init__(self):
        self.db = Database()
        self.db.connect()

    def close(self):
        self.db.close()

    # =====================================================
    # LIVESTOCK (Create, Read, Update, Delete, Search)
    # =====================================================

    def id_number_exists(self, id_number, exclude_id=None):
        """Check if an identification number is already used."""
        if exclude_id is None:
            row = self.db.fetch_one(
                "SELECT livestock_id FROM livestock WHERE id_number = %s",
                (id_number,))
        else:
            row = self.db.fetch_one(
                "SELECT livestock_id FROM livestock "
                "WHERE id_number = %s AND livestock_id != %s",
                (id_number, exclude_id))
        return row is not None

    def add_livestock(self, livestock):
        """Add a new livestock record. Returns the new livestock_id."""
        error = livestock.validate()
        if error != "":
            raise ValueError(error)
        if self.id_number_exists(livestock.id_number):
            raise ValueError("That identification number already exists.")

        query = ("INSERT INTO livestock (id_number, name, type, breed, sex, "
                 "birth_date, weight, health_status, date_acquired) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
        return self.db.execute_query(query, livestock.to_tuple())

    def get_all_livestock(self):
        """Return all livestock records."""
        query = f"SELECT {self.LIVESTOCK_COLUMNS} FROM livestock ORDER BY livestock_id"
        return [clean_row(row) for row in self.db.fetch_all(query)]

    def get_livestock_by_id(self, livestock_id):
        """Return one livestock record (or None)."""
        query = f"SELECT {self.LIVESTOCK_COLUMNS} FROM livestock WHERE livestock_id = %s"
        row = self.db.fetch_one(query, (livestock_id,))
        if row is None:
            return None
        return clean_row(row)

    def update_livestock(self, livestock):
        """Update an existing livestock record."""
        error = livestock.validate()
        if error != "":
            raise ValueError(error)
        if self.id_number_exists(livestock.id_number, livestock.livestock_id):
            raise ValueError("That identification number already exists.")

        query = ("UPDATE livestock SET id_number = %s, name = %s, type = %s, "
                 "breed = %s, sex = %s, birth_date = %s, weight = %s, "
                 "health_status = %s, date_acquired = %s "
                 "WHERE livestock_id = %s")
        params = livestock.to_tuple() + (livestock.livestock_id,)
        self.db.execute_query(query, params)

    def delete_livestock(self, livestock_id):
        """Delete a livestock record. Its health and breeding records
        are deleted too (ON DELETE CASCADE)."""
        self.db.execute_query(
            "DELETE FROM livestock WHERE livestock_id = %s", (livestock_id,))

    def search_livestock(self, keyword="", livestock_type="All", health_status="All"):
        """Search by ID number or name, and filter by type and health status."""
        query = f"SELECT {self.LIVESTOCK_COLUMNS} FROM livestock WHERE 1=1"
        params = []

        keyword = keyword.strip()
        if keyword != "":
            query += " AND (id_number LIKE %s OR name LIKE %s)"
            params.append("%" + keyword + "%")
            params.append("%" + keyword + "%")
        if livestock_type != "All":
            query += " AND type = %s"
            params.append(livestock_type)
        if health_status != "All":
            query += " AND health_status = %s"
            params.append(health_status)

        query += " ORDER BY livestock_id"
        rows = self.db.fetch_all(query, tuple(params))
        return [clean_row(row) for row in rows]

    def get_livestock_choices(self):
        """Return (livestock_id, id_number, name) for dropdown lists."""
        return self.db.fetch_all(
            "SELECT livestock_id, id_number, name FROM livestock ORDER BY id_number")

    # =====================================================
    # HEALTH RECORDS
    # =====================================================

    def _check_health(self, livestock_id, record_date, illness, treatment, vaccination):
        if not livestock_id:
            raise ValueError("Please select a livestock.")
        if not is_valid_date(record_date, required=True):
            raise ValueError("Record date is required (YYYY-MM-DD).")
        if (illness.strip() == "" and treatment.strip() == ""
                and vaccination.strip() == ""):
            raise ValueError("Enter an illness, treatment, or vaccination.")

    def add_health_record(self, livestock_id, record_date, illness,
                          treatment, vaccination, notes):
        self._check_health(livestock_id, record_date, illness, treatment, vaccination)
        query = ("INSERT INTO health_records (livestock_id, record_date, illness, "
                 "treatment, vaccination, notes) VALUES (%s, %s, %s, %s, %s, %s)")
        return self.db.execute_query(query, (
            livestock_id, record_date.strip(), illness.strip(),
            treatment.strip(), vaccination.strip(), notes.strip()))

    def get_health_records(self):
        """Return: health_id, id_number, name, record_date, illness,
        treatment, vaccination, notes"""
        query = ("SELECT h.health_id, l.id_number, l.name, h.record_date, "
                 "h.illness, h.treatment, h.vaccination, h.notes "
                 "FROM health_records h "
                 "JOIN livestock l ON h.livestock_id = l.livestock_id "
                 "ORDER BY h.record_date DESC, h.health_id DESC")
        return [clean_row(row) for row in self.db.fetch_all(query)]

    def update_health_record(self, health_id, record_date, illness,
                             treatment, vaccination, notes):
        self._check_health(1, record_date, illness, treatment, vaccination)
        query = ("UPDATE health_records SET record_date = %s, illness = %s, "
                 "treatment = %s, vaccination = %s, notes = %s "
                 "WHERE health_id = %s")
        self.db.execute_query(query, (
            record_date.strip(), illness.strip(), treatment.strip(),
            vaccination.strip(), notes.strip(), health_id))

    def delete_health_record(self, health_id):
        self.db.execute_query(
            "DELETE FROM health_records WHERE health_id = %s", (health_id,))

    # =====================================================
    # BREEDING RECORDS
    # =====================================================

    def _check_breeding(self, livestock_id, breeding_date, status, expected_date):
        if not livestock_id:
            raise ValueError("Please select a livestock.")
        if not is_valid_date(breeding_date, required=True):
            raise ValueError("Breeding date is required (YYYY-MM-DD).")
        if status not in self.BREEDING_STATUSES:
            raise ValueError("Please select a valid breeding status.")
        if not is_valid_date(expected_date):
            raise ValueError("Expected delivery date must be YYYY-MM-DD.")

    def add_breeding_record(self, livestock_id, breeding_date, status,
                            expected_date, notes):
        self._check_breeding(livestock_id, breeding_date, status, expected_date)
        query = ("INSERT INTO breeding_records (livestock_id, breeding_date, "
                 "breeding_status, expected_delivery_date, notes) "
                 "VALUES (%s, %s, %s, %s, %s)")
        return self.db.execute_query(query, (
            livestock_id, breeding_date.strip(), status,
            expected_date.strip() or None, notes.strip()))

    def get_breeding_records(self):
        """Return: breeding_id, id_number, name, breeding_date,
        breeding_status, expected_delivery_date, notes"""
        query = ("SELECT b.breeding_id, l.id_number, l.name, b.breeding_date, "
                 "b.breeding_status, b.expected_delivery_date, b.notes "
                 "FROM breeding_records b "
                 "JOIN livestock l ON b.livestock_id = l.livestock_id "
                 "ORDER BY b.breeding_date DESC, b.breeding_id DESC")
        return [clean_row(row) for row in self.db.fetch_all(query)]

    def update_breeding_record(self, breeding_id, breeding_date, status,
                               expected_date, notes):
        self._check_breeding(1, breeding_date, status, expected_date)
        query = ("UPDATE breeding_records SET breeding_date = %s, "
                 "breeding_status = %s, expected_delivery_date = %s, notes = %s "
                 "WHERE breeding_id = %s")
        self.db.execute_query(query, (
            breeding_date.strip(), status, expected_date.strip() or None,
            notes.strip(), breeding_id))

    def delete_breeding_record(self, breeding_id):
        self.db.execute_query(
            "DELETE FROM breeding_records WHERE breeding_id = %s", (breeding_id,))

    # =====================================================
    # EXPENSES (total_amount = quantity x unit_cost)
    # =====================================================

    def _check_expense(self, expense_date, category, description, quantity, unit_cost):
        """Validate the expense and return (quantity, unit_cost, total_amount)."""
        if not is_valid_date(expense_date, required=True):
            raise ValueError("Expense date is required (YYYY-MM-DD).")
        if category not in self.EXPENSE_CATEGORIES:
            raise ValueError("Please select a valid category.")
        if description.strip() == "":
            raise ValueError("Description is required.")
        try:
            quantity = float(quantity)
            unit_cost = float(unit_cost)
        except ValueError:
            raise ValueError("Quantity and unit cost must be numbers.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative.")
        total_amount = round(quantity * unit_cost, 2)
        return quantity, unit_cost, total_amount

    def add_expense(self, expense_date, category, description,
                    quantity, unit_cost, notes):
        quantity, unit_cost, total = self._check_expense(
            expense_date, category, description, quantity, unit_cost)
        query = ("INSERT INTO expenses (expense_date, category, description, "
                 "quantity, unit_cost, total_amount, notes) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        return self.db.execute_query(query, (
            expense_date.strip(), category, description.strip(),
            quantity, unit_cost, total, notes.strip()))

    def get_expenses(self, category="All"):
        """Return: expense_id, expense_date, category, description,
        quantity, unit_cost, total_amount, notes"""
        query = ("SELECT expense_id, expense_date, category, description, "
                 "quantity, unit_cost, total_amount, notes FROM expenses")
        params = ()
        if category != "All":
            query += " WHERE category = %s"
            params = (category,)
        query += " ORDER BY expense_date DESC, expense_id DESC"
        return [clean_row(row) for row in self.db.fetch_all(query, params)]

    def update_expense(self, expense_id, expense_date, category, description,
                       quantity, unit_cost, notes):
        quantity, unit_cost, total = self._check_expense(
            expense_date, category, description, quantity, unit_cost)
        query = ("UPDATE expenses SET expense_date = %s, category = %s, "
                 "description = %s, quantity = %s, unit_cost = %s, "
                 "total_amount = %s, notes = %s WHERE expense_id = %s")
        self.db.execute_query(query, (
            expense_date.strip(), category, description.strip(),
            quantity, unit_cost, total, notes.strip(), expense_id))

    def delete_expense(self, expense_id):
        self.db.execute_query(
            "DELETE FROM expenses WHERE expense_id = %s", (expense_id,))

    # =====================================================
    # DASHBOARD SUMMARIES
    # =====================================================

    def get_total_livestock(self):
        row = self.db.fetch_one("SELECT COUNT(*) FROM livestock")
        return row[0]

    def get_count_by_type(self):
        """Return a dictionary like {"Cattle": 2, "Pig": 1, "Goat": 0, ...}."""
        counts = {}
        for livestock_type in Livestock.TYPES:
            counts[livestock_type] = 0
        rows = self.db.fetch_all(
            "SELECT type, COUNT(*) FROM livestock GROUP BY type")
        for livestock_type, count in rows:
            counts[livestock_type] = count
        return counts

    def get_total_expenses(self):
        """Return the total of all recorded expenses as a number."""
        row = self.db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM expenses")
        return float(row[0])

    def get_dashboard_summary(self):
        """Return all dashboard numbers in one dictionary."""
        return {
            "total_livestock": self.get_total_livestock(),
            "count_by_type": self.get_count_by_type(),
            "total_expenses": self.get_total_expenses()
        }
