
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import Database
from users import make_user
from utils import parse_datetime, valid_date, valid_time


class SmartCampusApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Smart Campus Booking System")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self.db = Database()
        self.current_user = None

        self.show_login()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def heading(self, parent, title, subtitle=None):
        ttk.Label(
            parent,
            text=title,
            font=("Arial", 18, "bold")
        ).pack(pady=(10, 5))

        if subtitle:
            ttk.Label(parent, text=subtitle).pack(pady=(0, 10))

    def make_tree(self, parent, columns, headings):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=8)

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=10
        )

        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=125, anchor="w")

        vertical = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(yscrollcommand=vertical.set)

        tree.pack(side="left", fill="both", expand=True)
        vertical.pack(side="right", fill="y")

        return tree

    def fill_tree(self, tree, rows):
        tree.delete(*tree.get_children())

        for row in rows:
            tree.insert("", "end", values=row)

    def show_login(self):
        self.clear()
        self.current_user = None

        frame = ttk.Frame(self, padding=30)
        frame.pack(expand=True)

        self.heading(
            frame,
            "Smart Campus Booking System",
            "Richfield Graduate Institution"
        )

        form = ttk.LabelFrame(frame, text="Login", padding=20)
        form.pack(pady=15)

        ttk.Label(form, text="Email:").grid(
            row=0, column=0, sticky="w", pady=8
        )
        email = ttk.Entry(form, width=38)
        email.grid(row=0, column=1, pady=8)

        ttk.Label(form, text="Password:").grid(
            row=1, column=0, sticky="w", pady=8
        )
        password = ttk.Entry(form, width=38, show="*")
        password.grid(row=1, column=1, pady=8)

        def login():
            row = self.db.authenticate(
                email.get(),
                password.get()
            )

            if row is None:
                messagebox.showerror(
                    "Login failed",
                    "Invalid email address or password."
                )
                return

            self.current_user = make_user(row)
            self.show_dashboard()

        ttk.Button(
            form,
            text="Login",
            command=login
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Button(
            form,
            text="Register as Lecturer",
            command=self.show_registration
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)

        ttk.Button(
            form,
            text="Change Password",
            command=self.show_change_password
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)

        ttk.Label(
            frame,
            text=(
                "Demonstration accounts\n"
                "Lecturer: lecturer@richfield.ac.za / Lecturer123!\n"
                "Administrator: admin@richfield.ac.za / Admin123!\n"
                "Operator: operator@richfield.ac.za / Operator123!"
            ),
            justify="center"
        ).pack(pady=12)

    def show_change_password(self):
        window = tk.Toplevel(self)
        window.title("Change Password")
        window.geometry("440x370")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        self.heading(
            frame,
            "Change Password",
            "Enter your email and current password to continue."
        )

        form = ttk.LabelFrame(frame, text="Password details", padding=12)
        form.pack(fill="x", pady=10)

        fields = {}

        labels = [
            "Email",
            "Current password",
            "New password",
            "Confirm new password"
        ]

        for index, label in enumerate(labels):
            ttk.Label(form, text=label + ":").grid(
                row=index, column=0, sticky="w", padx=5, pady=7
            )

            entry = ttk.Entry(
                form,
                width=27,
                show="*" if "password" in label.lower() else ""
            )
            entry.grid(row=index, column=1, padx=5, pady=7)
            fields[label] = entry

        def save_password():
            email = fields["Email"].get().strip()
            current = fields["Current password"].get()
            new = fields["New password"].get()
            confirmation = fields["Confirm new password"].get()

            if not all([email, current, new, confirmation]):
                messagebox.showwarning(
                    "Missing information",
                    "Complete all fields.",
                    parent=window
                )
                return

            if new != confirmation:
                messagebox.showwarning(
                    "Password mismatch",
                    "The new password and confirmation do not match.",
                    parent=window
                )
                return

            if len(new) < 8:
                messagebox.showwarning(
                    "Password too short",
                    "Your new password must contain at least 8 characters.",
                    parent=window
                )
                return

            success, message = self.db.change_password(
                email, current, new
            )

            if success:
                messagebox.showinfo(
                    "Password changed",
                    message,
                    parent=window
                )
                window.destroy()
            else:
                messagebox.showerror(
                    "Unable to change password",
                    message,
                    parent=window
                )

        ttk.Button(
            form,
            text="Save New Password",
            command=save_password
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Button(
            form,
            text="Cancel",
            command=window.destroy
        ).grid(row=5, column=0, columnspan=2, sticky="ew")

        fields["Email"].focus_set()

    def show_registration(self):
        self.clear()

        frame = ttk.Frame(self, padding=30)
        frame.pack(expand=True)

        self.heading(frame, "Lecturer Registration")

        form = ttk.LabelFrame(frame, text="Account details", padding=20)
        form.pack(pady=15)

        fields = {}

        for index, label in enumerate(
            ["Full name", "Email", "Password", "Confirm password"]
        ):
            ttk.Label(form, text=label + ":").grid(
                row=index, column=0, sticky="w", pady=8
            )

            entry = ttk.Entry(
                form,
                width=35,
                show="*" if "Password" in label else ""
            )
            entry.grid(row=index, column=1, pady=8)
            fields[label] = entry

        def register():
            name = fields["Full name"].get().strip()
            email = fields["Email"].get().strip()
            password = fields["Password"].get()
            confirmation = fields["Confirm password"].get()

            if not name or not email or not password or not confirmation:
                messagebox.showwarning(
                    "Validation",
                    "Complete all fields."
                )
                return

            if password != confirmation:
                messagebox.showwarning(
                    "Validation",
                    "The passwords do not match."
                )
                return

            success, message = self.db.register_lecturer(
                name, email, password
            )

            if success:
                messagebox.showinfo("Registration", message)
                self.show_login()
            else:
                messagebox.showerror("Registration", message)

        ttk.Button(
            form,
            text="Create Account",
            command=register
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Button(
            form,
            text="Back to Login",
            command=self.show_login
        ).grid(row=5, column=0, columnspan=2, sticky="ew")

    def show_dashboard(self):
        self.clear()

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(
            top,
            text=(
                f"User: {self.current_user.full_name} | "
                f"Role: {self.current_user.role}"
            ),
            font=("Arial", 12, "bold")
        ).pack(side="left")

        ttk.Button(
            top,
            text="Logout",
            command=self.show_login
        ).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        if self.current_user.role == "Lecturer":
            self.build_lecturer_tabs(notebook)

        elif self.current_user.role == "Campus Administrator":
            self.build_admin_tabs(notebook)

        elif self.current_user.role == "System Operator":
            self.build_operator_tabs(notebook)

    def build_lecturer_tabs(self, notebook):
        booking_tab = ttk.Frame(notebook, padding=12)
        history_tab = ttk.Frame(notebook, padding=12)

        notebook.add(booking_tab, text="Book Resource")
        notebook.add(history_tab, text="My Bookings")

        self.build_booking_tab(booking_tab)
        self.build_history_tab(history_tab)

    def build_booking_tab(self, parent):
        campuses = self.db.campuses()

        campus_map = {
            campus["name"]: campus["campus_id"]
            for campus in campuses
        }

        ttk.Label(parent, text="Select campus:").pack(anchor="w")

        campus_box = ttk.Combobox(
            parent,
            values=list(campus_map.keys()),
            state="readonly",
            width=35
        )
        campus_box.pack(anchor="w", pady=5)

        policy_label = ttk.Label(
            parent,
            text="Select a campus to view its booking policy.",
            wraplength=850
        )
        policy_label.pack(anchor="w", pady=5)

        form = ttk.LabelFrame(parent, text="Booking details", padding=10)
        form.pack(fill="x", pady=8)

        date_entry = ttk.Entry(form, width=18)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        time_entry = ttk.Entry(form, width=12)
        time_entry.insert(0, "09:00")

        duration_entry = ttk.Entry(form, width=10)
        duration_entry.insert(0, "1")

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(
            row=0, column=0, sticky="w", padx=4, pady=5
        )
        date_entry.grid(row=1, column=0, padx=4, pady=5)

        ttk.Label(form, text="Start time (HH:MM)").grid(
            row=0, column=1, sticky="w", padx=4, pady=5
        )
        time_entry.grid(row=1, column=1, padx=4, pady=5)

        ttk.Label(form, text="Duration in hours").grid(
            row=0, column=2, sticky="w", padx=4, pady=5
        )
        duration_entry.grid(row=1, column=2, padx=4, pady=5)

        ttk.Label(form, text="Resource").grid(
            row=0, column=3, sticky="w", padx=4, pady=5
        )

        resource_box = ttk.Combobox(
            form,
            state="readonly",
            width=35
        )
        resource_box.grid(row=1, column=3, padx=4, pady=5)

        resource_map = {}

        tree = self.make_tree(
            parent,
            ("id", "name", "type", "availability"),
            ("Resource ID", "Resource", "Type", "Availability")
        )

        def refresh_resources(event=None):
            campus_name = campus_box.get()

            if not campus_name:
                return

            campus_id = campus_map[campus_name]
            campus = self.db.campus(campus_id)

            policy_label.config(
                text=(
                    f"Active campus: {campus['name']} | "
                    f"Maximum duration: {campus['max_hours']} hour(s) | "
                    f"Hours: {campus['open_time']}–{campus['close_time']} | "
                    f"Rule: {campus['priority_rule']}"
                )
            )

            resource_map.clear()
            values = []

            for resource in self.db.resources(campus_id):
                label = (
                    f"{resource['resource_id']} - "
                    f"{resource['resource_name']}"
                )
                values.append(label)
                resource_map[label] = resource["resource_id"]

            resource_box["values"] = values

            if values:
                resource_box.current(0)

            refresh_availability()

        def refresh_availability():
            if not campus_box.get():
                return

            try:
                campus_id = campus_map[campus_box.get()]
                date_text = date_entry.get().strip()
                time_text = time_entry.get().strip()
                duration = float(duration_entry.get())

                if not valid_date(date_text) or not valid_time(time_text):
                    raise ValueError("Use the required date and time formats.")

                start = parse_datetime(date_text, time_text)
                campus = self.db.campus(campus_id)

                from campus import BookingPolicy

                policy = BookingPolicy(
                    campus["max_hours"],
                    campus["open_time"],
                    campus["close_time"],
                    campus["priority_rule"]
                )

                accepted, _ = policy.validate(start, duration)
                rows = []

                for resource in self.db.resources(campus_id):
                    available = (
                        start > datetime.now()
                        and accepted
                        and self.db.is_available(
                            resource["resource_id"],
                            date_text,
                            start,
                            duration
                        )
                    )

                    rows.append((
                        resource["resource_id"],
                        resource["resource_name"],
                        resource["resource_type"],
                        "Available" if available else "Unavailable"
                    ))

                self.fill_tree(tree, rows)

            except (ValueError, TypeError) as error:
                messagebox.showwarning(
                    "Invalid booking details", str(error)
                )

        def create_booking():
            try:
                campus_id = campus_map[campus_box.get()]
                resource_id = resource_map[resource_box.get()]
                date_text = date_entry.get().strip()
                time_text = time_entry.get().strip()
                duration = float(duration_entry.get())

                if not valid_date(date_text) or not valid_time(time_text):
                    raise ValueError("Enter a valid date and time.")

                success, message = self.db.create_booking(
                    self.current_user.user_id,
                    resource_id,
                    campus_id,
                    date_text,
                    time_text,
                    duration
                )

                if success:
                    messagebox.showinfo("Booking", message)
                else:
                    messagebox.showerror("Booking rejected", message)

                refresh_availability()

            except (ValueError, KeyError):
                messagebox.showwarning(
                    "Invalid booking",
                    "Select a campus and resource and enter valid details."
                )

        campus_box.bind("<<ComboboxSelected>>", refresh_resources)

        ttk.Button(
            form,
            text="Check Availability",
            command=refresh_availability
        ).grid(row=2, column=0, columnspan=2, pady=8, sticky="ew")

        ttk.Button(
            form,
            text="Create Booking",
            command=create_booking
        ).grid(row=2, column=2, columnspan=2, pady=8, sticky="ew")

        if campuses:
            campus_box.current(0)
            refresh_resources()

    def build_history_tab(self, parent):
        tree = self.make_tree(
            parent,
            ("id", "campus", "resource", "date", "time", "duration", "status"),
            (
                "Booking ID", "Campus", "Resource",
                "Date", "Start", "Hours", "Status"
            )
        )

        def refresh():
            rows = []

            for booking in self.db.user_bookings(
                self.current_user.user_id
            ):
                rows.append((
                    booking["booking_id"],
                    booking["campus_name"],
                    booking["resource_name"],
                    booking["booking_date"],
                    booking["start_time"],
                    booking["duration"],
                    booking["status"]
                ))

            self.fill_tree(tree, rows)

        def cancel():
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Select booking",
                    "Select a booking to cancel."
                )
                return

            booking_id = tree.item(selected[0])["values"][0]

            success, message = self.db.cancel_booking(
                booking_id,
                self.current_user.user_id
            )

            if success:
                messagebox.showinfo("Cancellation", message)
            else:
                messagebox.showerror("Cancellation", message)

            refresh()

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=8)

        ttk.Button(
            buttons,
            text="Refresh History",
            command=refresh
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Cancel Selected Future Booking",
            command=cancel
        ).pack(side="left", padx=5)

        refresh()

    def build_admin_tabs(self, notebook):
        campus = self.db.campus(self.current_user.campus_id)

        if campus is None:
            ttk.Label(
                notebook,
                text="No campus is assigned to this administrator."
            ).pack(pady=20)
            return

        resource_tab = ttk.Frame(notebook, padding=12)
        booking_tab = ttk.Frame(notebook, padding=12)
        report_tab = ttk.Frame(notebook, padding=12)

        notebook.add(resource_tab, text="Manage Resources")
        notebook.add(booking_tab, text="Campus Bookings")
        notebook.add(report_tab, text="Campus Report")

        self.build_admin_resources(resource_tab, campus)
        self.build_admin_bookings(booking_tab, campus)
        self.build_campus_report(report_tab, campus)

    def build_admin_resources(self, parent, campus):
        ttk.Label(
            parent,
            text=f"Managing resources for {campus['name']}",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=5)

        form = ttk.LabelFrame(parent, text="Resource details", padding=10)
        form.pack(fill="x", pady=8)

        entries = {}

        for index, label in enumerate(
            ["Resource ID", "Resource name", "Resource type"]
        ):
            ttk.Label(form, text=label).grid(
                row=index, column=0, sticky="w", pady=4
            )

            entry = ttk.Entry(form, width=35)
            entry.grid(row=index, column=1, pady=4)
            entries[label] = entry

        tree = self.make_tree(
            parent,
            ("id", "name", "type"),
            ("Resource ID", "Name", "Type")
        )

        def refresh():
            rows = [
                (
                    resource["resource_id"],
                    resource["resource_name"],
                    resource["resource_type"]
                )
                for resource in self.db.resources(campus["campus_id"])
            ]
            self.fill_tree(tree, rows)

        def select_resource(event=None):
            selected = tree.selection()

            if not selected:
                return

            values = tree.item(selected[0])["values"]

            entries["Resource ID"].delete(0, "end")
            entries["Resource ID"].insert(0, values[0])

            entries["Resource name"].delete(0, "end")
            entries["Resource name"].insert(0, values[1])

            entries["Resource type"].delete(0, "end")
            entries["Resource type"].insert(0, values[2])

        def add():
            success, message = self.db.add_resource(
                entries["Resource ID"].get(),
                campus["campus_id"],
                entries["Resource name"].get(),
                entries["Resource type"].get()
            )

            if success:
                messagebox.showinfo("Resource", message)
                refresh()
            else:
                messagebox.showerror("Resource", message)

        def update():
            success, message = self.db.update_resource(
                entries["Resource ID"].get().strip().upper(),
                entries["Resource name"].get(),
                entries["Resource type"].get()
            )

            if success:
                messagebox.showinfo("Resource", message)
                refresh()
            else:
                messagebox.showerror("Resource", message)

        def delete():
            resource_id = entries["Resource ID"].get().strip().upper()

            if not resource_id:
                messagebox.showwarning(
                    "Resource",
                    "Enter or select a resource ID."
                )
                return

            if not messagebox.askyesno(
                "Confirm removal",
                f"Remove resource {resource_id}?"
            ):
                return

            success, message = self.db.delete_resource(resource_id)

            if success:
                messagebox.showinfo("Resource", message)
                refresh()
            else:
                messagebox.showerror("Resource", message)

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=5)

        ttk.Button(
            buttons, text="Add", command=add
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Update", command=update
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Remove", command=delete
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Refresh", command=refresh
        ).pack(side="left", padx=4)

        tree.bind("<<TreeviewSelect>>", select_resource)
        refresh()

    def build_admin_bookings(self, parent, campus):
        tree = self.make_tree(
            parent,
            ("id", "lecturer", "resource", "date", "time", "hours", "status"),
            (
                "Booking ID", "Lecturer", "Resource",
                "Date", "Start", "Hours", "Status"
            )
        )

        def refresh():
            rows = []

            for booking in self.db.campus_bookings(campus["campus_id"]):
                rows.append((
                    booking["booking_id"],
                    booking["full_name"],
                    booking["resource_name"],
                    booking["booking_date"],
                    booking["start_time"],
                    booking["duration"],
                    booking["status"]
                ))

            self.fill_tree(tree, rows)

        ttk.Button(
            parent,
            text="Refresh Campus Bookings",
            command=refresh
        ).pack(anchor="w", pady=5)

        refresh()

    def build_campus_report(self, parent, campus):
        tree = self.make_tree(
            parent,
            ("campus", "total", "most_used", "average"),
            ("Campus", "Active Bookings", "Most Used Resource", "Average Hours")
        )

        def refresh():
            total, most_used, average = self.db.campus_report(
                campus["campus_id"]
            )

            rows = [(
                campus["name"],
                total,
                most_used["resource_name"] if most_used else "No bookings",
                round(average, 2) if average is not None else 0
            )]

            self.fill_tree(tree, rows)

        ttk.Button(
            parent,
            text="Generate Campus Report",
            command=refresh
        ).pack(anchor="w", pady=5)

        refresh()

    def build_operator_tabs(self, notebook):
        report_tab = ttk.Frame(notebook, padding=12)
        bookings_tab = ttk.Frame(notebook, padding=12)
        resources_tab = ttk.Frame(notebook, padding=12)

        notebook.add(report_tab, text="Cross-Campus Reports")
        notebook.add(bookings_tab, text="All Bookings")
        notebook.add(resources_tab, text="All Resources")

        self.build_operator_reports(report_tab)
        self.build_operator_bookings(bookings_tab)
        self.build_operator_resources(resources_tab)

    def build_operator_reports(self, parent):
        tree = self.make_tree(
            parent,
            ("campus", "total", "most_used", "average"),
            ("Campus", "Active Bookings", "Most Used Resource", "Average Hours")
        )

        def refresh():
            rows = []

            for report in self.db.cross_campus_report():
                rows.append((
                    report["campus"],
                    report["total_bookings"],
                    report["most_used"],
                    report["average_duration"]
                ))

            self.fill_tree(tree, rows)

        ttk.Button(
            parent,
            text="Generate Cross-Campus Report",
            command=refresh
        ).pack(anchor="w", pady=5)

        refresh()

    def build_operator_bookings(self, parent):
        tree = self.make_tree(
            parent,
            ("id", "campus", "lecturer", "resource", "date", "time", "status"),
            (
                "Booking ID", "Campus", "Lecturer",
                "Resource", "Date", "Start", "Status"
            )
        )

        def refresh():
            rows = []

            for booking in self.db.campus_bookings():
                rows.append((
                    booking["booking_id"],
                    booking["campus_name"],
                    booking["full_name"],
                    booking["resource_name"],
                    booking["booking_date"],
                    booking["start_time"],
                    booking["status"]
                ))

            self.fill_tree(tree, rows)

        ttk.Button(
            parent,
            text="Refresh All Bookings",
            command=refresh
        ).pack(anchor="w", pady=5)

        refresh()

    def build_operator_resources(self, parent):
        tree = self.make_tree(
            parent,
            ("id", "campus", "name", "type"),
            ("Resource ID", "Campus", "Resource", "Type")
        )

        def refresh():
            rows = [
                (
                    resource["resource_id"],
                    resource["campus_name"],
                    resource["resource_name"],
                    resource["resource_type"]
                )
                for resource in self.db.resources()
            ]

            self.fill_tree(tree, rows)

        ttk.Button(
            parent,
            text="Refresh All Resources",
            command=refresh
        ).pack(anchor="w", pady=5)

        refresh()
