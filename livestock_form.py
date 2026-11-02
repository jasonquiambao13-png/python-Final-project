# livestock_form.py
# A pop-up form for adding and updating livestock records.

import tkinter as tk
from tkinter import ttk, messagebox

from mysql.connector import Error

from livestock import Livestock


class LivestockForm(tk.Toplevel):
    """Form window for adding or updating one livestock record.

    parent         - the main window
    manager        - a LivestockManager object
    on_save        - function to call after a successful save (refreshes the table)
    livestock_data - a record tuple when updating, or None when adding
    """

    def __init__(self, parent, manager, on_save, livestock_data=None):
        super().__init__(parent)
        self.manager = manager
        self.on_save = on_save
        self.livestock_data = livestock_data
        self.livestock_id = None

        if livestock_data is None:
            self.title("Add Livestock")
        else:
            self.title("Update Livestock")
            self.livestock_id = livestock_data[0]

        self.resizable(False, False)
        self.transient(parent)   # stay on top of the main window
        self.grab_set()          # block the main window until this form closes

        self.create_widgets()

        if livestock_data is not None:
            self.fill_form()

    def create_widgets(self):
        """Create the labels, entry fields, dropdowns, and buttons."""
        frame = ttk.Frame(self, padding=15)
        frame.grid(row=0, column=0)

        # Variables that hold what the user types or selects
        self.id_number_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar(value=Livestock.TYPES[0])
        self.breed_var = tk.StringVar()
        self.sex_var = tk.StringVar(value=Livestock.SEXES[0])
        self.birth_date_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.health_status_var = tk.StringVar(value=Livestock.HEALTH_STATUSES[0])
        self.date_acquired_var = tk.StringVar()

        # Row 0: ID number
        ttk.Label(frame, text="ID Number:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.id_number_var, width=30).grid(row=0, column=1, pady=5)

        # Row 1: Name
        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=5)

        # Row 2: Type (dropdown)
        ttk.Label(frame, text="Type:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.type_var, values=Livestock.TYPES,
                     state="readonly", width=27).grid(row=2, column=1, pady=5)

        # Row 3: Breed
        ttk.Label(frame, text="Breed:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.breed_var, width=30).grid(row=3, column=1, pady=5)

        # Row 4: Sex (dropdown)
        ttk.Label(frame, text="Sex:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.sex_var, values=Livestock.SEXES,
                     state="readonly", width=27).grid(row=4, column=1, pady=5)

        # Row 5: Birth date
        ttk.Label(frame, text="Birth Date:").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.birth_date_var, width=30).grid(row=5, column=1, pady=5)

        # Row 6: Weight
        ttk.Label(frame, text="Weight (kg):").grid(row=6, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.weight_var, width=30).grid(row=6, column=1, pady=5)

        # Row 7: Health status (dropdown)
        ttk.Label(frame, text="Health Status:").grid(row=7, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.health_status_var,
                     values=Livestock.HEALTH_STATUSES,
                     state="readonly", width=27).grid(row=7, column=1, pady=5)

        # Row 8: Date acquired
        ttk.Label(frame, text="Date Acquired:").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.date_acquired_var, width=30).grid(row=8, column=1, pady=5)

        # Row 9: Date format hint
        ttk.Label(frame, text="Dates use the format YYYY-MM-DD (example: 2026-10-15)",
                  foreground="gray").grid(row=9, column=0, columnspan=2, pady=(5, 10))

        # Row 10: Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=10, column=0, columnspan=2)
        ttk.Button(button_frame, text="Save", command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5)

    def fill_form(self):
        """Put the existing record's values into the fields (for updating)."""
        data = self.livestock_data
        # data order: livestock_id, id_number, name, type, breed, sex,
        #             birth_date, weight, health_status, date_acquired
        self.id_number_var.set(data[1])
        self.name_var.set(data[2])
        self.type_var.set(data[3])
        self.breed_var.set(data[4])
        self.sex_var.set(data[5])
        self.birth_date_var.set(data[6])
        self.weight_var.set(data[7])
        self.health_status_var.set(data[8])
        self.date_acquired_var.set(data[9])

    def save(self):
        """Create a Livestock object from the fields and save it."""
        livestock = Livestock(
            id_number=self.id_number_var.get(),
            name=self.name_var.get(),
            type=self.type_var.get(),
            breed=self.breed_var.get(),
            sex=self.sex_var.get(),
            birth_date=self.birth_date_var.get(),
            weight=self.weight_var.get(),
            health_status=self.health_status_var.get(),
            date_acquired=self.date_acquired_var.get(),
            livestock_id=self.livestock_id
        )

        try:
            if self.livestock_id is None:
                self.manager.add_livestock(livestock)
                messagebox.showinfo("Success", "Livestock added successfully.", parent=self)
            else:
                self.manager.update_livestock(livestock)
                messagebox.showinfo("Success", "Livestock updated successfully.", parent=self)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self)
            return
        except Error as e:
            messagebox.showerror("Database Error", str(e), parent=self)
            return

        self.on_save()   # refresh the table in the dashboard
        self.destroy()   # close the form
