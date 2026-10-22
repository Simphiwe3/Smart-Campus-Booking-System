
import sqlite3
from datetime import datetime, timedelta

from utils import hash_password, parse_datetime


DB_NAME = "smart_campus.db"


class Database:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS campuses (
                    campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    max_hours REAL NOT NULL,
                    open_time TEXT NOT NULL,
                    close_time TEXT NOT NULL,
                    priority_rule TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (
                        role IN (
                            'Lecturer',
                            'Campus Administrator',
                            'System Operator'
                        )
                    ),
                    campus_id INTEGER,
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id)
                );

                CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    campus_id INTEGER NOT NULL,
                    resource_name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id)
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    resource_id TEXT NOT NULL,
                    campus_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration REAL NOT NULL CHECK (duration > 0),
                    status TEXT NOT NULL DEFAULT 'Active'
                        CHECK (status IN ('Active', 'Cancelled')),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users(user_id),
                    FOREIGN KEY (resource_id)
                        REFERENCES resources(resource_id),
                    FOREIGN KEY (campus_id)
                        REFERENCES campuses(campus_id)
                );
            """)

            campuses = [
                (
                    "Johannesburg Campus",
                    2,
                    "08:00",
                    "18:00",
                    "Standard teaching bookings"
                ),
                (
                    "Pretoria Campus",
                    3,
                    "08:00",
                    "20:00",
                    "Extended booking hours"
                ),
                (
                    "Cape Town Campus",
                    4,
                    "09:00",
                    "17:00",
                    "Daytime booking restrictions"
                )
            ]

            for campus in campuses:
                connection.execute("""
                    INSERT OR IGNORE INTO campuses
                    (name, max_hours, open_time, close_time, priority_rule)
                    VALUES (?, ?, ?, ?, ?)
                """, campus)

            campus_ids = {
                row["name"]: row["campus_id"]
                for row in connection.execute(
                    "SELECT campus_id, name FROM campuses"
                )
            }

            resources = [
                (
                    "JHB-LAB-01",
                    campus_ids["Johannesburg Campus"],
                    "Computer Laboratory 1",
                    "Computer Lab"
                ),
                (
                    "JHB-PROJ-01",
                    campus_ids["Johannesburg Campus"],
                    "Multimedia Projector 1",
                    "Projector"
                ),
                (
                    "JHB-SEM-01",
                    campus_ids["Johannesburg Campus"],
                    "Seminar Room 1",
                    "Seminar Room"
                ),
                (
                    "PTA-LAB-01",
                    campus_ids["Pretoria Campus"],
                    "Computer Laboratory 1",
                    "Computer Lab"
                ),
                (
                    "PTA-PROJ-01",
                    campus_ids["Pretoria Campus"],
                    "Multimedia Projector 1",
                    "Projector"
                ),
                (
                    "PTA-SEM-01",
                    campus_ids["Pretoria Campus"],
                    "Seminar Room 1",
                    "Seminar Room"
                ),
                (
                    "CPT-LAB-01",
                    campus_ids["Cape Town Campus"],
                    "Computer Laboratory 1",
                    "Computer Lab"
                ),
                (
                    "CPT-PROJ-01",
                    campus_ids["Cape Town Campus"],
                    "Multimedia Projector 1",
                    "Projector"
                ),
                (
                    "CPT-SEM-01",
                    campus_ids["Cape Town Campus"],
                    "Seminar Room 1",
                    "Seminar Room"
                )
            ]

            for resource in resources:
                connection.execute("""
                    INSERT OR IGNORE INTO resources
                    (resource_id, campus_id, resource_name, resource_type)
                    VALUES (?, ?, ?, ?)
                """, resource)

            demo_users = [
                (
                    "Demo Lecturer",
                    "lecturer@richfield.ac.za",
                    hash_password("Lecturer123!"),
                    "Lecturer",
                    None
                ),
                (
                    "Campus Administrator",
                    "admin@richfield.ac.za",
                    hash_password("Admin123!"),
                    "Campus Administrator",
                    campus_ids["Johannesburg Campus"]
                ),
                (
                    "System Operator",
                    "operator@richfield.ac.za",
                    hash_password("Operator123!"),
                    "System Operator",
                    None
                )
            ]

            for user in demo_users:
                connection.execute("""
                    INSERT OR IGNORE INTO users
                    (full_name, email, password_hash, role, campus_id)
                    VALUES (?, ?, ?, ?, ?)
                """, user)

    def authenticate(self, email, password):
        with self.connect() as connection:
            return connection.execute("""
                SELECT *
                FROM users
                WHERE lower(email) = lower(?)
                  AND password_hash = ?
            """, (
                email.strip(),
                hash_password(password)
            )).fetchone()

    def change_password(
        self, email, current_password, new_password
    ):
        if not email.strip():
            return False, "Email address is required."

        if len(new_password) < 8:
            return False, (
                "The new password must contain at least 8 characters."
            )

        if current_password == new_password:
            return False, (
                "Your new password must be different from your current password."
            )

        with self.connect() as connection:
            user = connection.execute("""
                SELECT user_id
                FROM users
                WHERE lower(email) = lower(?)
                  AND password_hash = ?
            """, (
                email.strip(),
                hash_password(current_password)
            )).fetchone()

            if user is None:
                return False, (
                    "The email address or current password is incorrect."
                )

            connection.execute("""
                UPDATE users
                SET password_hash = ?
                WHERE user_id = ?
            """, (
                hash_password(new_password),
                user["user_id"]
            ))

        return True, "Your password has been changed successfully."

    def register_lecturer(self, full_name, email, password):
        if not full_name.strip():
            return False, "Full name is required."

        if "@" not in email or "." not in email:
            return False, "Enter a valid email address."

        if len(password) < 8:
            return False, "Password must contain at least 8 characters."

        try:
            with self.connect() as connection:
                connection.execute("""
                    INSERT INTO users
                    (full_name, email, password_hash, role, campus_id)
                    VALUES (?, ?, ?, 'Lecturer', NULL)
                """, (
                    full_name.strip(),
                    email.strip(),
                    hash_password(password)
                ))

            return True, "Lecturer account created successfully."

        except sqlite3.IntegrityError:
            return False, "That email address is already registered."

    def campuses(self):
        with self.connect() as connection:
            return connection.execute("""
                SELECT *
                FROM campuses
                ORDER BY name
            """).fetchall()

    def campus(self, campus_id):
        with self.connect() as connection:
            return connection.execute("""
                SELECT *
                FROM campuses
                WHERE campus_id = ?
            """, (campus_id,)).fetchone()

    def resources(self, campus_id=None):
        with self.connect() as connection:
            if campus_id is None:
                return connection.execute("""
                    SELECT r.*, c.name AS campus_name
                    FROM resources r
                    JOIN campuses c ON c.campus_id = r.campus_id
                    ORDER BY c.name, r.resource_name
                """).fetchall()

            return connection.execute("""
                SELECT *
                FROM resources
                WHERE campus_id = ?
                ORDER BY resource_name
            """, (campus_id,)).fetchall()

    def add_resource(self, resource_id, campus_id, name, resource_type):
        if not all([
            resource_id.strip(),
            name.strip(),
            resource_type.strip()
        ]):
            return False, "All resource fields are required."

        try:
            with self.connect() as connection:
                connection.execute("""
                    INSERT INTO resources
                    (resource_id, campus_id, resource_name, resource_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    resource_id.strip().upper(),
                    campus_id,
                    name.strip(),
                    resource_type.strip()
                ))

            return True, "Resource added successfully."

        except sqlite3.IntegrityError:
            return False, (
                "Resource ID already exists or the selected campus is invalid."
            )

    def update_resource(self, resource_id, name, resource_type):
        if not name.strip() or not resource_type.strip():
            return False, "Resource name and type are required."

        with self.connect() as connection:
            result = connection.execute("""
                UPDATE resources
                SET resource_name = ?, resource_type = ?
                WHERE resource_id = ?
            """, (
                name.strip(),
                resource_type.strip(),
                resource_id
            ))

            if result.rowcount == 0:
                return False, "Resource not found."

        return True, "Resource updated successfully."

    def delete_resource(self, resource_id):
        with self.connect() as connection:
            active = connection.execute("""
                SELECT COUNT(*) AS total
                FROM bookings
                WHERE resource_id = ? AND status = 'Active'
            """, (resource_id,)).fetchone()["total"]

            if active:
                return False, (
                    "Cancel active bookings before removing this resource."
                )

            try:
                result = connection.execute("""
                    DELETE FROM resources
                    WHERE resource_id = ?
                """, (resource_id,))

                if result.rowcount == 0:
                    return False, "Resource not found."

            except sqlite3.IntegrityError:
                return False, (
                    "This resource has booking history and cannot be removed. "
                    "Keep the record to preserve historical information."
                )

        return True, "Resource removed successfully."

    def is_available(
        self, resource_id, booking_date, start_datetime, duration
    ):
        end_datetime = start_datetime + timedelta(hours=duration)

        with self.connect() as connection:
            resource = connection.execute("""
                SELECT campus_id
                FROM resources
                WHERE resource_id = ?
            """, (resource_id,)).fetchone()

            if resource is None:
                return False

            bookings = connection.execute("""
                SELECT booking_date, start_time, duration
                FROM bookings
                WHERE resource_id = ?
                  AND status = 'Active'
                  AND booking_date = ?
            """, (resource_id, booking_date)).fetchall()

        for booking in bookings:
            existing_start = parse_datetime(
                booking["booking_date"],
                booking["start_time"]
            )

            existing_end = existing_start + timedelta(
                hours=booking["duration"]
            )

            if (
                start_datetime < existing_end
                and end_datetime > existing_start
            ):
                return False

        return True

    def create_booking(
        self,
        user_id,
        resource_id,
        campus_id,
        booking_date,
        start_time,
        duration
    ):
        try:
            duration = float(duration)
            start_datetime = parse_datetime(booking_date, start_time)
        except (ValueError, TypeError):
            return False, "Enter a valid date, time and duration."

        if start_datetime <= datetime.now():
            return False, "Bookings must start in the future."

        if duration <= 0:
            return False, "Duration must be greater than zero."

        campus = self.campus(campus_id)

        if campus is None:
            return False, "Select a valid campus."

        with self.connect() as connection:
            resource = connection.execute("""
                SELECT *
                FROM resources
                WHERE resource_id = ? AND campus_id = ?
            """, (resource_id, campus_id)).fetchone()

        if resource is None:
            return False, "The resource does not belong to this campus."

        from campus import BookingPolicy

        policy = BookingPolicy(
            campus["max_hours"],
            campus["open_time"],
            campus["close_time"],
            campus["priority_rule"]
        )

        accepted, message = policy.validate(start_datetime, duration)

        if not accepted:
            return False, message

        if not self.is_available(
            resource_id,
            booking_date,
            start_datetime,
            duration
        ):
            return False, (
                "This resource is already booked for an overlapping period."
            )

        with self.connect() as connection:
            connection.execute("""
                INSERT INTO bookings
                (
                    user_id, resource_id, campus_id,
                    booking_date, start_time, duration,
                    status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Active', ?)
            """, (
                user_id,
                resource_id,
                campus_id,
                booking_date,
                start_time,
                duration,
                datetime.now().isoformat(timespec="seconds")
            ))

        return True, "Booking created successfully."

    def user_bookings(self, user_id):
        with self.connect() as connection:
            return connection.execute("""
                SELECT b.*, r.resource_name, r.resource_type,
                       c.name AS campus_name
                FROM bookings b
                JOIN resources r ON r.resource_id = b.resource_id
                JOIN campuses c ON c.campus_id = b.campus_id
                WHERE b.user_id = ?
                ORDER BY b.booking_date DESC, b.start_time DESC
            """, (user_id,)).fetchall()

    def cancel_booking(self, booking_id, user_id):
        with self.connect() as connection:
            booking = connection.execute("""
                SELECT booking_date, start_time
                FROM bookings
                WHERE booking_id = ?
                  AND user_id = ?
                  AND status = 'Active'
            """, (booking_id, user_id)).fetchone()

            if booking is None:
                return False, "Active booking not found."

            start_datetime = parse_datetime(
                booking["booking_date"],
                booking["start_time"]
            )

            if start_datetime <= datetime.now():
                return False, "Only future bookings can be cancelled."

            connection.execute("""
                UPDATE bookings
                SET status = 'Cancelled'
                WHERE booking_id = ?
                  AND user_id = ?
                  AND status = 'Active'
            """, (booking_id, user_id))

        return True, "Booking cancelled successfully."

    def campus_bookings(self, campus_id=None):
        with self.connect() as connection:
            query = """
                SELECT b.*, u.full_name, u.email,
                       r.resource_name, c.name AS campus_name
                FROM bookings b
                JOIN users u ON u.user_id = b.user_id
                JOIN resources r ON r.resource_id = b.resource_id
                JOIN campuses c ON c.campus_id = b.campus_id
            """

            if campus_id is not None:
                query += " WHERE b.campus_id = ?"
                query += " ORDER BY b.booking_date DESC, b.start_time DESC"
                return connection.execute(query, (campus_id,)).fetchall()

            query += " ORDER BY b.booking_date DESC, b.start_time DESC"
            return connection.execute(query).fetchall()

    def campus_report(self, campus_id):
        with self.connect() as connection:
            total = connection.execute("""
                SELECT COUNT(*) AS total
                FROM bookings
                WHERE campus_id = ? AND status = 'Active'
            """, (campus_id,)).fetchone()["total"]

            most_used = connection.execute("""
                SELECT r.resource_name, COUNT(*) AS usage_count
                FROM bookings b
                JOIN resources r ON r.resource_id = b.resource_id
                WHERE b.campus_id = ? AND b.status = 'Active'
                GROUP BY r.resource_id, r.resource_name
                ORDER BY usage_count DESC, r.resource_name
                LIMIT 1
            """, (campus_id,)).fetchone()

            average = connection.execute("""
                SELECT AVG(duration) AS average_duration
                FROM bookings
                WHERE campus_id = ? AND status = 'Active'
            """, (campus_id,)).fetchone()["average_duration"]

        return total, most_used, average

    def cross_campus_report(self):
        report = []

        for campus in self.campuses():
            total, most_used, average = self.campus_report(
                campus["campus_id"]
            )

            report.append({
                "campus": campus["name"],
                "total_bookings": total,
                "most_used": (
                    most_used["resource_name"] if most_used else "No bookings"
                ),
                "average_duration": (
                    round(average, 2) if average is not None else 0
                )
            })

        return report
