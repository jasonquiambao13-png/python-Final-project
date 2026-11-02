import tkinter as tk
from tkinter import messagebox

from mysql.connector import Error

from livestock_manager import LivestockManager
from dashboard import Dashboard


def main():
    # Try to connect to the database first
    try:
        manager = LivestockManager()
    except Error as e:
        # Show the error in a message box (needs a hidden root window)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Connection Failed",
            "Could not connect to MySQL.\n\n"
            "Check that:\n"
            "1. MySQL is running\n"
            "2. The password in config.py is correct\n"
            "3. You ran sql/database.sql in MySQL Workbench\n\n"
            f"Details: {e}")
        root.destroy()
        return

    app = Dashboard(manager)
    app.mainloop()


if __name__ == "__main__":
    main()
