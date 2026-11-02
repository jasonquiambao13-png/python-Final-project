# dashboard.py
# The main window: dashboard summary, livestock table with search/filter,
# and tabs for health records, breeding records, and expenses.

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from mysql.connector import Error

from livestock import Livestock
from livestock_manager import LivestockManager
from livestock_form import LivestockForm


class Dashboard(tk.Tk):
    """Main application window."""

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

        self.title("Livestock Management System")
        self.geometry("1150x720")
        self.minsize(1000, 600)

        # Stores used by the tabs
        self.livestock_choices = {}   # "CT-001 - Bessie" -> livestock_id
        self.health_rows = {}         # health_id -> row data
        self.breeding_rows = {}       # breeding_id -> row data
        self.expense_rows = {}        # expense_id -> row data

        self.create_summary()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_livestock_tab()
        self.create_health_tab()
        self.create_breeding_tab()
        self.create_expense_tab()

        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # =====================================================
    # HELPER METHODS (used by all tabs)
    # =====================================================

    def add_entry(self, parent, label, variable, row, column, width=28):
        """Place a label and an entry field in a grid."""
        ttk.Label(parent, text=label).grid(row=row, column=column * 2,
                                           sticky="w", padx=5, pady=4)
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=column * 2 + 1, sticky="w", padx=5, pady=4)
        return entry

    def add_combo(self, parent, label, variable, values, row, column, width=26):
        """Place a label and a dropdown (Combobox) in a grid."""
        ttk.Label(parent, text=label).grid(row=row, column=column * 2,
                                           sticky="w", padx=5, pady=4)
        combo = ttk.Combobox(parent, textvariable=variable, values=values,
                             state="readonly", width=width)
        combo.grid(row=row, column=column * 2 + 1, sticky="w", padx=5, pady=4)
        return combo

    def add_buttons(self, parent, row, add_cmd, update_cmd, delete_cmd, clear_cmd):
        """Place the Add / Update / Delete / Clear buttons."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=4, pady=6)
        ttk.Button(frame, text="Add", command=add_cmd).grid(row=0, column=0, padx=4)
        ttk.Button(frame, text="Update", command=update_cmd).grid(row=0, column=1, padx=4)
        ttk.Button(frame, text="Delete", command=delete_cmd).grid(row=0, column=2, padx=4)
        ttk.Button(frame, text="Clear", command=clear_cmd).grid(row=0, column=3, padx=4)

    def create_table(self, parent, columns, widths):
        """Create a Treeview table with a scrollbar."""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(8, 0))

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            selectmode="browse")
        for name, width in zip(columns, widths):
            tree.heading(name, text=name)
            tree.column(name, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def fill_table(self, tree, rows, store=None):
        """Show rows in a table. The first value of each row is used as the item ID.
        If a dictionary is given, the rows are also saved in it."""
        tree.delete(*tree.get_children())
        if store is not None:
            store.clear()
        for row in rows:
            tree.insert("", "end", iid=row[0], values=row)
            if store is not None:
                store[row[0]] = row

    def get_selected(self, tree, message):
        """Return the selected row's ID, or None (with a warning) if nothing is selected."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", message)
            return None
        return selected[0]

    def show_db_error(self, error):
        messagebox.showerror("Database Error", str(error))

    # =====================================================
    # DASHBOARD SUMMARY (always visible at the top)
    # =====================================================

    def create_summary(self):
        frame = ttk.LabelFrame(self, text="Dashboard Summary", padding=10)
        frame.pack(fill="x", padx=10, pady=(10, 0))
        frame.columnconfigure(1, weight=1)

        self.total_var = tk.StringVar()
        self.type_summary_var = tk.StringVar()
        self.expense_summary_var = tk.StringVar()

        ttk.Label(frame, textvariable=self.total_var,
                  font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.expense_summary_var,
                  font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="e")
        ttk.Label(frame, textvariable=self.type_summary_var).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def refresh_summary(self):
        summary = self.manager.get_dashboard_summary()
        self.total_var.set(f"Total Livestock: {summary['total_livestock']}")

        parts = []
        for livestock_type, count in summary["count_by_type"].items():
            parts.append(f"{livestock_type}: {count}")
        self.type_summary_var.set("By Type:   " + "   |   ".join(parts))

        self.expense_summary_var.set(
            f"Total Expenses: PHP {summary['total_expenses']:,.2f}")

    def refresh_choices(self):
        """Reload the livestock dropdown lists used by the health and breeding forms."""
        self.livestock_choices = {}
        for livestock_id, id_number, name in self.manager.get_livestock_choices():
            self.livestock_choices[f"{id_number} - {name}"] = livestock_id

        names = list(self.livestock_choices.keys())
        self.h_livestock_combo["values"] = names
        self.b_livestock_combo["values"] = names

    def refresh_all(self):
        """Reload the summary and every table."""
        try:
            self.refresh_summary()
            self.refresh_choices()
            self.load_livestock()
            self.load_health()
            self.load_breeding()
            self.load_expenses()
        except Error as e:
            self.show_db_error(e)

    # =====================================================
    # LIVESTOCK TAB
    # =====================================================

    def create_livestock_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Livestock")

        # --- Search and filter controls ---
        search_frame = ttk.LabelFrame(tab, text="Search and Filter", padding=8)
        search_frame.pack(fill="x")

        self.search_var = tk.StringVar()
        self.filter_type_var = tk.StringVar(value="All")
        self.filter_status_var = tk.StringVar(value="All")

        ttk.Label(search_frame, text="ID Number / Name:").grid(row=0, column=0, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=22)
        search_entry.grid(row=0, column=1, padx=5)
        search_entry.bind("<Return>", self.search_livestock)

        ttk.Label(search_frame, text="Type:").grid(row=0, column=2, padx=5)
        type_combo = ttk.Combobox(search_frame, textvariable=self.filter_type_var,
                                  values=["All"] + Livestock.TYPES,
                                  state="readonly", width=12)
        type_combo.grid(row=0, column=3, padx=5)
        type_combo.bind("<<ComboboxSelected>>", self.search_livestock)

        ttk.Label(search_frame, text="Health Status:").grid(row=0, column=4, padx=5)
        status_combo = ttk.Combobox(search_frame, textvariable=self.filter_status_var,
                                    values=["All"] + Livestock.HEALTH_STATUSES,
                                    state="readonly", width=15)
        status_combo.grid(row=0, column=5, padx=5)
        status_combo.bind("<<ComboboxSelected>>", self.search_livestock)

        ttk.Button(search_frame, text="Search",
                   command=self.search_livestock).grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="Clear",
                   command=self.clear_search).grid(row=0, column=7, padx=5)

        # --- Action buttons ---
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(button_frame, text="Add",
                   command=self.add_livestock).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Update",
                   command=self.update_livestock).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Delete",
                   command=self.delete_livestock).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Refresh",
                   command=self.refresh_all).pack(side="left", padx=4)

        # --- Livestock table ---
        columns = ("ID", "ID Number", "Name", "Type", "Breed", "Sex",
                   "Birth Date", "Weight (kg)", "Health Status", "Date Acquired")
        widths = (40, 90, 110, 80, 110, 70, 95, 85, 110, 100)
        self.livestock_tree = self.create_table(tab, columns, widths)

    def load_livestock(self):
        rows = self.manager.search_livestock(
            self.search_var.get(),
            self.filter_type_var.get(),
            self.filter_status_var.get())
        self.fill_table(self.livestock_tree, rows)

    def search_livestock(self, event=None):
        try:
            self.load_livestock()
        except Error as e:
            self.show_db_error(e)

    def clear_search(self):
        self.search_var.set("")
        self.filter_type_var.set("All")
        self.filter_status_var.set("All")
        self.search_livestock()

    def add_livestock(self):
        LivestockForm(self, self.manager, self.refresh_all)

    def update_livestock(self):
        selected = self.get_selected(self.livestock_tree,
                                     "Please select a livestock record to update.")
        if selected is None:
            return
        try:
            data = self.manager.get_livestock_by_id(int(selected))
        except Error as e:
            self.show_db_error(e)
            return
        if data is None:
            messagebox.showerror("Error", "That record no longer exists.")
            self.refresh_all()
            return
        LivestockForm(self, self.manager, self.refresh_all, data)

    def delete_livestock(self):
        selected = self.get_selected(self.livestock_tree,
                                     "Please select a livestock record to delete.")
        if selected is None:
            return
        values = self.livestock_tree.item(selected)["values"]
        name = values[2]
        answer = messagebox.askyesno(
            "Confirm Delete",
            f"Delete {name}?\nIts health and breeding records will also be deleted.")
        if not answer:
            return
        try:
            self.manager.delete_livestock(int(selected))
            messagebox.showinfo("Success", "Livestock deleted successfully.")
            self.refresh_all()
        except Error as e:
            self.show_db_error(e)

    # =====================================================
    # HEALTH RECORDS TAB
    # =====================================================

    def create_health_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Health Records")

        form = ttk.LabelFrame(tab, text="Health Record Form", padding=8)
        form.pack(fill="x")

        self.h_livestock_var = tk.StringVar()
        self.h_date_var = tk.StringVar()
        self.h_illness_var = tk.StringVar()
        self.h_treatment_var = tk.StringVar()
        self.h_vaccination_var = tk.StringVar()
        self.h_notes_var = tk.StringVar()

        self.h_livestock_combo = self.add_combo(
            form, "Livestock:", self.h_livestock_var, [], 0, 0)
        self.add_entry(form, "Record Date:", self.h_date_var, 0, 1)
        self.add_entry(form, "Illness:", self.h_illness_var, 1, 0)
        self.add_entry(form, "Treatment:", self.h_treatment_var, 1, 1)
        self.add_entry(form, "Vaccination:", self.h_vaccination_var, 2, 0)
        self.add_entry(form, "Notes:", self.h_notes_var, 2, 1)
        ttk.Label(form, text="Dates use YYYY-MM-DD. To update a record, select it in "
                             "the table, edit the fields, then click Update.",
                  foreground="gray").grid(row=3, column=0, columnspan=4, sticky="w", padx=5)
        self.add_buttons(form, 4, self.add_health, self.update_health,
                         self.delete_health, self.clear_health_form)

        columns = ("ID", "ID Number", "Name", "Date", "Illness",
                   "Treatment", "Vaccination", "Notes")
        widths = (40, 90, 110, 95, 140, 150, 140, 200)
        self.health_tree = self.create_table(tab, columns, widths)
        self.health_tree.bind("<<TreeviewSelect>>", self.on_health_select)

        self.clear_health_form()

    def load_health(self):
        self.fill_table(self.health_tree, self.manager.get_health_records(),
                        self.health_rows)

    def clear_health_form(self):
        self.h_livestock_var.set("")
        self.h_date_var.set(str(date.today()))
        self.h_illness_var.set("")
        self.h_treatment_var.set("")
        self.h_vaccination_var.set("")
        self.h_notes_var.set("")
        self.health_tree.selection_remove(self.health_tree.selection())

    def on_health_select(self, event=None):
        selected = self.health_tree.selection()
        if not selected:
            return
        row = self.health_rows[selected[0]]
        # row: health_id, id_number, name, record_date, illness, treatment, vaccination, notes
        self.h_livestock_var.set(f"{row[1]} - {row[2]}")
        self.h_date_var.set(row[3])
        self.h_illness_var.set(row[4])
        self.h_treatment_var.set(row[5])
        self.h_vaccination_var.set(row[6])
        self.h_notes_var.set(row[7])

    def add_health(self):
        livestock_id = self.livestock_choices.get(self.h_livestock_var.get())
        try:
            self.manager.add_health_record(
                livestock_id, self.h_date_var.get(), self.h_illness_var.get(),
                self.h_treatment_var.get(), self.h_vaccination_var.get(),
                self.h_notes_var.get())
            messagebox.showinfo("Success", "Health record added successfully.")
            self.clear_health_form()
            self.load_health()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def update_health(self):
        selected = self.get_selected(self.health_tree,
                                     "Please select a health record to update.")
        if selected is None:
            return
        try:
            self.manager.update_health_record(
                int(selected), self.h_date_var.get(), self.h_illness_var.get(),
                self.h_treatment_var.get(), self.h_vaccination_var.get(),
                self.h_notes_var.get())
            messagebox.showinfo("Success", "Health record updated successfully.")
            self.clear_health_form()
            self.load_health()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def delete_health(self):
        selected = self.get_selected(self.health_tree,
                                     "Please select a health record to delete.")
        if selected is None:
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this health record?"):
            return
        try:
            self.manager.delete_health_record(int(selected))
            messagebox.showinfo("Success", "Health record deleted successfully.")
            self.clear_health_form()
            self.load_health()
        except Error as e:
            self.show_db_error(e)

    # =====================================================
    # BREEDING RECORDS TAB
    # =====================================================

    def create_breeding_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Breeding Records")

        form = ttk.LabelFrame(tab, text="Breeding Record Form", padding=8)
        form.pack(fill="x")

        self.b_livestock_var = tk.StringVar()
        self.b_date_var = tk.StringVar()
        self.b_status_var = tk.StringVar(value=LivestockManager.BREEDING_STATUSES[0])
        self.b_expected_var = tk.StringVar()
        self.b_notes_var = tk.StringVar()

        self.b_livestock_combo = self.add_combo(
            form, "Livestock:", self.b_livestock_var, [], 0, 0)
        self.add_entry(form, "Breeding Date:", self.b_date_var, 0, 1)
        self.add_combo(form, "Status:", self.b_status_var,
                       LivestockManager.BREEDING_STATUSES, 1, 0)
        self.add_entry(form, "Expected Delivery:", self.b_expected_var, 1, 1)
        self.add_entry(form, "Notes:", self.b_notes_var, 2, 0)
        ttk.Label(form, text="Dates use YYYY-MM-DD. Expected delivery is optional. "
                             "To update a record, select it in the table first.",
                  foreground="gray").grid(row=3, column=0, columnspan=4, sticky="w", padx=5)
        self.add_buttons(form, 4, self.add_breeding, self.update_breeding,
                         self.delete_breeding, self.clear_breeding_form)

        columns = ("ID", "ID Number", "Name", "Breeding Date", "Status",
                   "Expected Delivery", "Notes")
        widths = (40, 90, 110, 110, 100, 120, 280)
        self.breeding_tree = self.create_table(tab, columns, widths)
        self.breeding_tree.bind("<<TreeviewSelect>>", self.on_breeding_select)

        self.clear_breeding_form()

    def load_breeding(self):
        self.fill_table(self.breeding_tree, self.manager.get_breeding_records(),
                        self.breeding_rows)

    def clear_breeding_form(self):
        self.b_livestock_var.set("")
        self.b_date_var.set(str(date.today()))
        self.b_status_var.set(LivestockManager.BREEDING_STATUSES[0])
        self.b_expected_var.set("")
        self.b_notes_var.set("")
        self.breeding_tree.selection_remove(self.breeding_tree.selection())

    def on_breeding_select(self, event=None):
        selected = self.breeding_tree.selection()
        if not selected:
            return
        row = self.breeding_rows[selected[0]]
        # row: breeding_id, id_number, name, breeding_date, status, expected, notes
        self.b_livestock_var.set(f"{row[1]} - {row[2]}")
        self.b_date_var.set(row[3])
        self.b_status_var.set(row[4])
        self.b_expected_var.set(row[5])
        self.b_notes_var.set(row[6])

    def add_breeding(self):
        livestock_id = self.livestock_choices.get(self.b_livestock_var.get())
        try:
            self.manager.add_breeding_record(
                livestock_id, self.b_date_var.get(), self.b_status_var.get(),
                self.b_expected_var.get(), self.b_notes_var.get())
            messagebox.showinfo("Success", "Breeding record added successfully.")
            self.clear_breeding_form()
            self.load_breeding()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def update_breeding(self):
        selected = self.get_selected(self.breeding_tree,
                                     "Please select a breeding record to update.")
        if selected is None:
            return
        try:
            self.manager.update_breeding_record(
                int(selected), self.b_date_var.get(), self.b_status_var.get(),
                self.b_expected_var.get(), self.b_notes_var.get())
            messagebox.showinfo("Success", "Breeding record updated successfully.")
            self.clear_breeding_form()
            self.load_breeding()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def delete_breeding(self):
        selected = self.get_selected(self.breeding_tree,
                                     "Please select a breeding record to delete.")
        if selected is None:
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this breeding record?"):
            return
        try:
            self.manager.delete_breeding_record(int(selected))
            messagebox.showinfo("Success", "Breeding record deleted successfully.")
            self.clear_breeding_form()
            self.load_breeding()
        except Error as e:
            self.show_db_error(e)

    # =====================================================
    # EXPENSES TAB
    # =====================================================

    def create_expense_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Expenses")

        form = ttk.LabelFrame(tab, text="Expense Form", padding=8)
        form.pack(fill="x")

        self.e_date_var = tk.StringVar()
        self.e_category_var = tk.StringVar(value=LivestockManager.EXPENSE_CATEGORIES[0])
        self.e_description_var = tk.StringVar()
        self.e_quantity_var = tk.StringVar()
        self.e_unit_cost_var = tk.StringVar()
        self.e_notes_var = tk.StringVar()
        self.e_total_var = tk.StringVar(value="0.00")

        self.add_entry(form, "Expense Date:", self.e_date_var, 0, 0)
        self.add_combo(form, "Category:", self.e_category_var,
                       LivestockManager.EXPENSE_CATEGORIES, 0, 1)
        self.add_entry(form, "Description:", self.e_description_var, 1, 0)
        quantity_entry = self.add_entry(form, "Quantity:", self.e_quantity_var, 1, 1)
        unit_cost_entry = self.add_entry(form, "Unit Cost:", self.e_unit_cost_var, 2, 0)
        self.add_entry(form, "Notes:", self.e_notes_var, 2, 1)

        # The total is calculated automatically (quantity x unit cost)
        quantity_entry.bind("<KeyRelease>", self.update_expense_total)
        unit_cost_entry.bind("<KeyRelease>", self.update_expense_total)
        ttk.Label(form, text="Total Amount (PHP):").grid(
            row=3, column=0, sticky="w", padx=5, pady=4)
        ttk.Label(form, textvariable=self.e_total_var,
                  font=("Arial", 11, "bold")).grid(row=3, column=1, sticky="w", padx=5)

        self.add_buttons(form, 4, self.add_expense, self.update_expense,
                         self.delete_expense, self.clear_expense_form)

        # --- Filter by category and listed total ---
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill="x", pady=(8, 0))
        self.e_filter_var = tk.StringVar(value="All")
        self.e_listed_total_var = tk.StringVar()

        ttk.Label(filter_frame, text="Filter by Category:").pack(side="left", padx=5)
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.e_filter_var,
                                    values=["All"] + LivestockManager.EXPENSE_CATEGORIES,
                                    state="readonly", width=14)
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_expenses)
        ttk.Label(filter_frame, textvariable=self.e_listed_total_var,
                  font=("Arial", 10, "bold")).pack(side="right", padx=5)

        columns = ("ID", "Date", "Category", "Description", "Quantity",
                   "Unit Cost", "Total Amount", "Notes")
        widths = (40, 95, 100, 220, 80, 90, 110, 250)
        self.expense_tree = self.create_table(tab, columns, widths)
        self.expense_tree.bind("<<TreeviewSelect>>", self.on_expense_select)

        self.clear_expense_form()

    def load_expenses(self):
        rows = self.manager.get_expenses(self.e_filter_var.get())
        self.fill_table(self.expense_tree, rows, self.expense_rows)

        listed_total = 0.0
        for row in rows:
            listed_total += float(row[6])
        self.e_listed_total_var.set(f"Total of Listed Expenses: PHP {listed_total:,.2f}")

    def filter_expenses(self, event=None):
        try:
            self.load_expenses()
        except Error as e:
            self.show_db_error(e)

    def update_expense_total(self, event=None):
        """Calculate quantity x unit cost while the user types."""
        try:
            total = float(self.e_quantity_var.get()) * float(self.e_unit_cost_var.get())
            self.e_total_var.set(f"{total:,.2f}")
        except ValueError:
            self.e_total_var.set("0.00")

    def clear_expense_form(self):
        self.e_date_var.set(str(date.today()))
        self.e_category_var.set(LivestockManager.EXPENSE_CATEGORIES[0])
        self.e_description_var.set("")
        self.e_quantity_var.set("")
        self.e_unit_cost_var.set("")
        self.e_notes_var.set("")
        self.e_total_var.set("0.00")
        self.expense_tree.selection_remove(self.expense_tree.selection())

    def on_expense_select(self, event=None):
        selected = self.expense_tree.selection()
        if not selected:
            return
        row = self.expense_rows[selected[0]]
        # row: expense_id, date, category, description, quantity, unit_cost, total, notes
        self.e_date_var.set(row[1])
        self.e_category_var.set(row[2])
        self.e_description_var.set(row[3])
        self.e_quantity_var.set(row[4])
        self.e_unit_cost_var.set(row[5])
        self.e_notes_var.set(row[7])
        self.update_expense_total()

    def add_expense(self):
        try:
            self.manager.add_expense(
                self.e_date_var.get(), self.e_category_var.get(),
                self.e_description_var.get(), self.e_quantity_var.get(),
                self.e_unit_cost_var.get(), self.e_notes_var.get())
            messagebox.showinfo("Success", "Expense added successfully.")
            self.clear_expense_form()
            self.refresh_summary()
            self.load_expenses()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def update_expense(self):
        selected = self.get_selected(self.expense_tree,
                                     "Please select an expense to update.")
        if selected is None:
            return
        try:
            self.manager.update_expense(
                int(selected), self.e_date_var.get(), self.e_category_var.get(),
                self.e_description_var.get(), self.e_quantity_var.get(),
                self.e_unit_cost_var.get(), self.e_notes_var.get())
            messagebox.showinfo("Success", "Expense updated successfully.")
            self.clear_expense_form()
            self.refresh_summary()
            self.load_expenses()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Error as e:
            self.show_db_error(e)

    def delete_expense(self):
        selected = self.get_selected(self.expense_tree,
                                     "Please select an expense to delete.")
        if selected is None:
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this expense?"):
            return
        try:
            self.manager.delete_expense(int(selected))
            messagebox.showinfo("Success", "Expense deleted successfully.")
            self.clear_expense_form()
            self.refresh_summary()
            self.load_expenses()
        except Error as e:
            self.show_db_error(e)

    # =====================================================
    # CLOSING THE APPLICATION
    # =====================================================

    def on_close(self):
        self.manager.close()
        self.destroy()
