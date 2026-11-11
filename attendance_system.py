
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
from datetime import datetime, date, time, timedelta
from calendar import monthrange

DB_NAME = "student_attendance.db"

# SCHOOL SETTINGS
SCHOOL_START = time(8, 0)
SCHOOL_END = time(15, 0)

# DEFAULT ADMIN LOGIN
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256(
    "admin123".encode()
).hexdigest()


# DATABASE CONNECTION
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# CREATE DATABASE TABLES
def setup_database():
    with connect_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                check_in TEXT NOT NULL,
                check_out TEXT,
                FOREIGN KEY(student_id)
                REFERENCES students(student_id)
                ON DELETE CASCADE
            )
        """)


def parse_dt(value):
    return datetime.fromisoformat(value)


def format_duration(minutes):
    minutes = max(0, int(round(minutes)))
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


# CALCULATE TIME PRESENT AND ABSENT
def school_minutes_for_day(student_id, day):

    if day.weekday() >= 5:
        return 0, 0

    opening = datetime.combine(day, SCHOOL_START)
    closing = datetime.combine(day, SCHOOL_END)

    scheduled = int(
        (closing - opening).total_seconds() / 60
    )

    present = 0

    with connect_db() as conn:

        records = conn.execute("""
            SELECT check_in, check_out
            FROM attendance
            WHERE student_id = ?
            AND date(check_in) = ?
        """, (student_id, day.isoformat())).fetchall()

    for check_in, check_out in records:

        start = max(parse_dt(check_in), opening)

        end = (
            min(parse_dt(check_out), closing)
            if check_out
            else min(datetime.now(), closing)
        )

        if end > start:
            present += int(
                (end - start).total_seconds() / 60
            )

    present = min(scheduled, present)
    absent = max(0, scheduled - present)

    return present, absent


# WEEKLY AND MONTHLY REPORT CALCULATION
def report_for_period(student_id, start_day, end_day):

    total_present = 0
    total_absent = 0

    current = start_day

    while current <= end_day:

        present, absent = school_minutes_for_day(
            student_id, current
        )

        total_present += present
        total_absent += absent

        current += timedelta(days=1)

    return total_present, total_absent


class AttendanceApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Student Attendance Management System"
        )

        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.detail_window = None
        self.detail_student_id = None

        self.login_screen()

    # CENTER WINDOWS
    def center_window(self, window, width, height):

        window.update_idletasks()

        x = (
            window.winfo_screenwidth() - width
        ) // 2

        y = (
            window.winfo_screenheight() - height
        ) // 2

        window.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def clear_root(self):

        for widget in self.root.winfo_children():
            widget.destroy()

    # ADMIN LOGIN PAGE
    def login_screen(self):

        self.clear_root()

        self.root.configure(bg="#edf2f7")

        self.center_window(self.root, 430, 390)

        panel = tk.Frame(
            self.root,
            bg="white",
            padx=35,
            pady=30
        )

        panel.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        tk.Label(
            panel,
            text="STUDENT ATTENDANCE",
            font=("Arial", 19, "bold"),
            bg="white",
            fg="#17365d"
        ).pack(pady=(0, 6))

        tk.Label(
            panel,
            text="Administrator Login",
            bg="white",
            fg="gray"
        ).pack(pady=(0, 22))

        tk.Label(
            panel,
            text="Username",
            bg="white"
        ).pack(anchor="w")

        self.username_entry = ttk.Entry(
            panel, width=34
        )

        self.username_entry.pack(
            pady=(5, 14), ipady=5
        )

        tk.Label(
            panel,
            text="Password",
            bg="white"
        ).pack(anchor="w")

        self.password_entry = ttk.Entry(
            panel,
            width=34,
            show="*"
        )

        self.password_entry.pack(
            pady=(5, 20), ipady=5
        )

        self.password_entry.bind(
            "<Return>",
            lambda event: self.login()
        )

        ttk.Button(
            panel,
            text="LOGIN",
            command=self.login
        ).pack(fill="x", ipady=6)

        tk.Label(
            panel,
            #text="Default: admin / admin123",
            bg="white",
            fg="gray"
        ).pack(pady=14)

        self.username_entry.focus_set()

    # VERIFY ADMIN
    def login(self):

        username = self.username_entry.get().strip()

        password = hashlib.sha256(
            self.password_entry.get().encode()
        ).hexdigest()

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD_HASH
        ):

            self.dashboard()

        else:

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

    # MAIN DASHBOARD
    def dashboard(self):

        self.clear_root()

        self.root.configure(bg="#f3f6fa")

        self.center_window(self.root, 1100, 700)

        header = tk.Frame(
            self.root,
            bg="#17365d",
            height=65
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="STUDENT ATTENDANCE MANAGEMENT",
            bg="#17365d",
            fg="white",
            font=("Arial", 17, "bold")
        ).pack(side="left", padx=20, pady=16)

        ttk.Button(
            header,
            text="Logout",
            command=self.login_screen
        ).pack(side="right", padx=20, pady=15)

        body = tk.Frame(
            self.root,
            bg="#f3f6fa",
            padx=18,
            pady=15
        )

        body.pack(fill="both", expand=True)

        # STUDENT REGISTRATION
        form = ttk.LabelFrame(
            body,
            text="Student Registration",
            padding=12
        )

        form.pack(fill="x", pady=(0, 12))

        self.sid_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.class_var = tk.StringVar()

        ttk.Label(
            form, text="Student ID"
        ).grid(row=0, column=0, sticky="w")

        ttk.Entry(
            form,
            textvariable=self.sid_var,
            width=20
        ).grid(row=1, column=0, padx=10, pady=5)

        ttk.Label(
            form, text="Full Name"
        ).grid(row=0, column=1, sticky="w")

        ttk.Entry(
            form,
            textvariable=self.name_var,
            width=34
        ).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(
            form, text="Class / Department"
        ).grid(row=0, column=2, sticky="w")

        ttk.Entry(
            form,
            textvariable=self.class_var,
            width=24
        ).grid(row=1, column=2, padx=10, pady=5)

        ttk.Button(
            form,
            text="Add Student",
            command=self.add_student
        ).grid(row=1, column=3, padx=5)

        # ATTENDANCE CONTROLS
        attendance_bar = ttk.LabelFrame(
            body,
            text="Student Entry and Exit",
            padding=10
        )

        attendance_bar.pack(
            fill="x", pady=(0, 12)
        )

        self.attendance_id_var = tk.StringVar()

        ttk.Label(
            attendance_bar,
            text="Student ID"
        ).pack(side="left")

        ttk.Entry(
            attendance_bar,
            textvariable=self.attendance_id_var,
            width=22
        ).pack(side="left", padx=10)

        ttk.Button(
            attendance_bar,
            text="CHECK IN",
            command=self.check_in
        ).pack(side="left", padx=5)

        ttk.Button(
            attendance_bar,
            text="CHECK OUT",
            command=self.check_out
        ).pack(side="left", padx=5)

        ttk.Button(
            attendance_bar,
            text="Weekly Report",
            command=lambda: self.show_report("week")
        ).pack(side="left", padx=(20, 5))

        ttk.Button(
            attendance_bar,
            text="Monthly Report",
            command=lambda: self.show_report("month")
        ).pack(side="left", padx=5)

        # STUDENT TABLE
        list_frame = ttk.LabelFrame(
            body,
            text="Registered Students",
            padding=10
        )

        list_frame.pack(fill="both", expand=True)

        columns = (
            "student_id",
            "full_name",
            "class_name",
            "status"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "student_id": "Student ID",
            "full_name": "Full Name",
            "class_name": "Class / Department",
            "status": "Current Status"
        }

        widths = {
            "student_id": 150,
            "full_name": 300,
            "class_name": 200,
            "status": 150
        }

        for col in columns:

            self.tree.heading(
                col,
                text=headings[col]
            )

            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ACTION BUTTONS
        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=10)

        ttk.Button(
            actions,
            text="Refresh from Database",
            command=self.refresh_students
        ).pack(side="left", padx=5)

        ttk.Button(
            actions,
            text="Student Details",
            command=self.open_student_details
        ).pack(side="left", padx=5)

        ttk.Button(
            actions,
            text="Delete Student and Records",
            command=self.delete_student
        ).pack(side="left", padx=5)

        self.refresh_students()

    # ADD STUDENT
    def add_student(self):

        sid = self.sid_var.get().strip()
        name = self.name_var.get().strip()
        class_name = self.class_var.get().strip()

        if not sid or not name or not class_name:

            messagebox.showwarning(
                "Missing Details",
                "Complete all student fields."
            )

            return

        try:

            with connect_db() as conn:

                conn.execute("""
                    INSERT INTO students
                    (student_id, full_name, class_name)
                    VALUES (?, ?, ?)
                """, (sid, name, class_name))

            self.sid_var.set("")
            self.name_var.set("")
            self.class_var.set("")

            self.refresh_students()

            messagebox.showinfo(
                "Success",
                "Student registered successfully."
            )

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Duplicate ID",
                "That student ID already exists."
            )

    # REFRESH STUDENTS
    def refresh_students(self):

        if not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        with connect_db() as conn:

            students = conn.execute("""
                SELECT student_id, full_name, class_name
                FROM students
                ORDER BY full_name
            """).fetchall()

            for sid, name, class_name in students:

                open_session = conn.execute("""
                    SELECT 1 FROM attendance
                    WHERE student_id = ?
                    AND check_out IS NULL
                    LIMIT 1
                """, (sid,)).fetchone()

                status = (
                    "INSIDE" if open_session
                    else "OUTSIDE"
                )

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        sid,
                        name,
                        class_name,
                        status
                    )
                )

        # Refresh an already-open details window.
        if (
            self.detail_window
            and self.detail_window.winfo_exists()
        ):
            self.refresh_detail_window()

    # GET SELECTED STUDENT
    def selected_student_id(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Select Student",
                "Please select a student first."
            )

            return None

        return self.tree.item(
            selected[0], "values"
        )[0]

    # CHECK IN
    def check_in(self):

        sid = self.attendance_id_var.get().strip()

        if not sid:

            messagebox.showwarning(
                "Student ID",
                "Enter a student ID."
            )

            return

        with connect_db() as conn:

            student = conn.execute("""
                SELECT full_name FROM students
                WHERE student_id = ?
            """, (sid,)).fetchone()

            if not student:

                messagebox.showerror(
                    "Not Found",
                    "Student ID does not exist."
                )

                return

            open_session = conn.execute("""
                SELECT record_id FROM attendance
                WHERE student_id = ?
                AND check_out IS NULL
            """, (sid,)).fetchone()

            if open_session:

                messagebox.showwarning(
                    "Already Inside",
                    "This student has already checked in."
                )

                return

            conn.execute("""
                INSERT INTO attendance
                (student_id, check_in)
                VALUES (?, ?)
            """, (
                sid,
                datetime.now().isoformat(timespec="seconds")
            ))

        self.refresh_students()

        messagebox.showinfo(
            "Checked In",
            f"{student[0]} checked in successfully."
        )

    # CHECK OUT
    def check_out(self):

        sid = self.attendance_id_var.get().strip()

        if not sid:

            messagebox.showwarning(
                "Student ID",
                "Enter a student ID."
            )

            return

        with connect_db() as conn:

            student = conn.execute("""
                SELECT full_name FROM students
                WHERE student_id = ?
            """, (sid,)).fetchone()

            if not student:

                messagebox.showerror(
                    "Not Found",
                    "Student ID does not exist."
                )

                return

            row = conn.execute("""
                SELECT record_id, check_in
                FROM attendance
                WHERE student_id = ?
                AND check_out IS NULL
                ORDER BY check_in DESC
                LIMIT 1
            """, (sid,)).fetchone()

            if not row:

                messagebox.showwarning(
                    "Not Checked In",
                    "This student has no open check-in record."
                )

                return

            now = datetime.now()

            conn.execute("""
                UPDATE attendance
                SET check_out = ?
                WHERE record_id = ?
            """, (
                now.isoformat(timespec="seconds"),
                row[0]
            ))

            duration = now - parse_dt(row[1])

        self.refresh_students()

        messagebox.showinfo(
            "Checked Out",
            f"{student[0]} checked out.\n"
            f"Time spent: "
            f"{format_duration(duration.total_seconds() / 60)}"
        )

    # OPEN STUDENT DETAILS WINDOW
    def open_student_details(self):

        sid = self.selected_student_id()

        if not sid:
            return

        if (
            self.detail_window
            and self.detail_window.winfo_exists()
        ):

            self.detail_student_id = sid

            self.refresh_detail_window()

            self.detail_window.deiconify()
            self.detail_window.lift()

            return

        self.detail_student_id = sid

        self.detail_window = tk.Toplevel(self.root)

        self.detail_window.title(
            "Student Details and Attendance History"
        )

        self.detail_window.geometry("850x480")

        self.center_window(
            self.detail_window, 850, 480
        )

        self.detail_heading = ttk.Label(
            self.detail_window,
            text="",
            font=("Arial", 13, "bold")
        )

        self.detail_heading.pack(
            anchor="w", padx=15, pady=12
        )

        columns = (
            "check_in",
            "check_out",
            "duration"
        )

        self.detail_tree = ttk.Treeview(
            self.detail_window,
            columns=columns,
            show="headings"
        )

        headings = {
            "check_in": "Check-In",
            "check_out": "Check-Out",
            "duration": "Time Spent"
        }

        widths = {
            "check_in": 280,
            "check_out": 280,
            "duration": 180
        }

        for col in columns:

            self.detail_tree.heading(
                col, text=headings[col]
            )

            self.detail_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.detail_tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=5
        )

        ttk.Button(
            self.detail_window,
            text="Refresh Details",
            command=self.refresh_detail_window
        ).pack(pady=10)

        self.detail_window.protocol(
            "WM_DELETE_WINDOW",
            self.close_detail_window
        )

        self.refresh_detail_window()

    # CLOSE DETAILS
    def close_detail_window(self):

        if (
            self.detail_window
            and self.detail_window.winfo_exists()
        ):
            self.detail_window.destroy()

        self.detail_window = None
        self.detail_student_id = None

    # REFRESH DETAILS FROM DATABASE
    def refresh_detail_window(self):

        if (
            not self.detail_window
            or not self.detail_window.winfo_exists()
        ):
            return

        sid = self.detail_student_id

        with connect_db() as conn:

            student = conn.execute("""
                SELECT full_name, class_name
                FROM students
                WHERE student_id = ?
            """, (sid,)).fetchone()

            records = conn.execute("""
                SELECT check_in, check_out
                FROM attendance
                WHERE student_id = ?
                ORDER BY check_in DESC
            """, (sid,)).fetchall()

        if not student:

            self.detail_heading.config(
                text="This student has been deleted."
            )

            for item in self.detail_tree.get_children():
                self.detail_tree.delete(item)

            return

        self.detail_heading.config(
            text=(
                f"{student[0]} | ID: {sid} | "
                f"Class: {student[1]}"
            )
        )

        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        for check_in, check_out in records:

            start = parse_dt(check_in)

            end = (
                parse_dt(check_out)
                if check_out
                else datetime.now()
            )

            duration = max(
                0,
                (end - start).total_seconds() / 60
            )

            self.detail_tree.insert(
                "",
                "end",
                values=(
                    start.strftime("%d %b %Y, %I:%M %p"),
                    parse_dt(check_out).strftime(
                        "%d %b %Y, %I:%M %p"
                    ) if check_out else "Still inside",
                    format_duration(duration)
                )
            )

    # DELETE STUDENT AND ALL ATTENDANCE RECORDS
    def delete_student(self):

        sid = self.selected_student_id()

        if not sid:
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Delete student {sid} and ALL attendance records?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        with connect_db() as conn:

            conn.execute("""
                DELETE FROM students
                WHERE student_id = ?
            """, (sid,))

        if self.detail_student_id == sid:
            self.refresh_detail_window()

        self.refresh_students()

        messagebox.showinfo(
            "Deleted",
            "Student and associated records deleted."
        )

    # WEEKLY AND MONTHLY REPORTS
    def show_report(self, period):

        sid = self.selected_student_id()

        if not sid:
            return

        today = date.today()

        if period == "week":

            start_day = today - timedelta(
                days=today.weekday()
            )

            end_day = start_day + timedelta(days=6)

            title = "Weekly Attendance Report"

        else:

            start_day = today.replace(day=1)

            end_day = today.replace(
                day=monthrange(
                    today.year, today.month
                )[1]
            )

            title = "Monthly Attendance Report"

        with connect_db() as conn:

            student = conn.execute("""
                SELECT full_name, class_name
                FROM students
                WHERE student_id = ?
            """, (sid,)).fetchone()

        if not student:

            messagebox.showerror(
                "Not Found",
                "Student no longer exists."
            )

            return

        present, absent = report_for_period(
            sid, start_day, end_day
        )

        scheduled_days = sum(
            1
            for offset in range(
                (end_day - start_day).days + 1
            )
            if (
                start_day + timedelta(days=offset)
            ).weekday() < 5
        )

        daily_minutes = int(
            (
                datetime.combine(today, SCHOOL_END)
                -
                datetime.combine(today, SCHOOL_START)
            ).total_seconds() / 60
        )

        scheduled_total = (
            scheduled_days * daily_minutes
        )

        messagebox.showinfo(
            title,
            f"Student: {student[0]}\n"
            f"Student ID: {sid}\n"
            f"Class: {student[1]}\n"
            f"Period: {start_day:%d %b %Y} "
            f"- {end_day:%d %b %Y}\n\n"
            f"Scheduled School Time: "
            f"{format_duration(scheduled_total)}\n"
            f"Total Time Present: "
            f"{format_duration(present)}\n"
            f"Total Absent Time: "
            f"{format_duration(absent)}"
        )


# START APPLICATION
if __name__ == "__main__":

    setup_database()

    root = tk.Tk()

    app = AttendanceApp(root)

    root.mainloop()
