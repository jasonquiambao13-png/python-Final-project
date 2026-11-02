import mysql.connector
from mysql.connector import Error



class Database:
    """Opens a MySQL connection and runs SQL queries."""

    def __init__(self):
        self.connection = None

    def connect(self):
        """Connect to MySQL. Raises an Error if it fails."""
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="adminjhon",
            database="livestock_management",
            port=3306
        )

    def close(self):
        """Close the connection if it is open."""
        if self.connection is not None and self.connection.is_connected():
            self.connection.close()

    def _ensure_connection(self):
        """Reconnect automatically if the connection was lost."""
        if self.connection is None or not self.connection.is_connected():
            self.connect()

    def execute_query(self, query, params=None):
        """Run INSERT, UPDATE, or DELETE.
        Returns the new ID for INSERT (or 0 for UPDATE/DELETE)."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        """Run SELECT and return all rows as a list of tuples."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        """Run SELECT and return only the first row (or None)."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()


# Quick connection test: run "python database.py" to check your settings.
if __name__ == "__main__":
    db = Database()
    try:
        db.connect()
        print("Connected to MySQL successfully!")
        count = db.fetch_one("SELECT COUNT(*) FROM livestock")
        print("Livestock records found:", count[0])
    except Error as e:
        print("Connection failed:", e)
    finally:
        db.close()
