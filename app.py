from flask import Flask, render_template, request, redirect, flash, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import csv
import io
import json

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL")
    or "sqlite:///" + os.path.join(basedir, "library.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["300 per day", "80 per hour"]
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# =========================
# DATABASE MODELS
# =========================
class Librarian(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(150))
    level = db.Column(db.String(10), default="100")
    checkins = db.relationship("CheckIn", backref="student", lazy=True)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    year = db.Column(db.String(10))
    isbn = db.Column(db.String(50))
    accession_no = db.Column(db.String(50))
    copies = db.Column(db.Integer, default=1)
    acquisition_type = db.Column(db.String(20))  # Purchased / Donated / Other
    acquisition_other = db.Column(db.String(150))
    remarks = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    date_deleted = db.Column(db.String(50))
    featured = db.Column(db.Boolean, default=False)
    loans = db.relationship("Loan", backref="book", lazy=True)


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    borrower_name = db.Column(db.String(150), nullable=False)
    level = db.Column(db.String(50))  # 100/200/300/400/Other
    level_other = db.Column(db.String(100))
    copy_number = db.Column(db.String(50))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    contact = db.Column(db.String(150))
    due_date = db.Column(db.String(50))
    renewal_date = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    date_returned = db.Column(db.String(50))


class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    timestamp = db.Column(
        db.String(50),
        default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M")
    )


@login_manager.user_loader
def load_user(user_id):
    return Librarian.query.get(int(user_id))


@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Too many attempts. Please wait a minute and try again.", "danger")
    return redirect(request.referrer or "/")


# =========================
# LIBRARIAN AUTH
# =========================
@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect("/register")

        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "danger")
            return redirect("/register")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect("/register")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect("/register")

        if Librarian.query.filter_by(email=email).first():
            flash("This email already has an account. Please login.", "danger")
            return redirect("/register")

        librarian = Librarian(name=name, email=email, password=generate_password_hash(password))
        db.session.add(librarian)
        db.session.commit()

        flash("Account created successfully.", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("6 per minute")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        librarian = Librarian.query.filter_by(email=email).first()
        if librarian is None or not check_password_hash(librarian.password, password):
            flash("Invalid email or password.", "danger")
            return redirect("/login")

        login_user(librarian)
        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# =========================
# PUBLIC CHECK-IN KIOSK (no login required)
# =========================
@app.route("/checkin", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def checkin():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()

        if not identifier:
            flash("Please enter your student ID or name.", "danger")
            return redirect("/checkin")

        student = Student.query.filter(
            (Student.student_id == identifier) | (Student.name.ilike(identifier))
        ).first()

        if student is None:
            flash(
                "We couldn't find that ID or name on file. Please see the librarian to be registered.",
                "danger"
            )
            return redirect("/checkin")

        check_in = CheckIn(student_id=student.id)
        db.session.add(check_in)
        db.session.commit()

        flash(f"Welcome, {student.name}! You're checked in.", "success")
        return redirect("/checkin")

    return render_template("checkin.html", students=Student.query.order_by(Student.name).all())


@app.route("/portal/login", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def portal_login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()

        student = Student.query.filter(
            (Student.student_id == identifier) | (Student.name.ilike(identifier))
        ).first()

        if student is None:
            flash("We couldn't find that Student ID. Please check and try again, or see the librarian.", "danger")
            return redirect("/portal/login")

        session["student_portal_id"] = student.id
        return redirect("/portal")

    return render_template("portal_login.html")


@app.route("/portal")
def student_portal():
    student_id = session.get("student_portal_id")
    if not student_id:
        return redirect("/portal/login")

    student = Student.query.get(student_id)
    if student is None:
        session.pop("student_portal_id", None)
        return redirect("/portal/login")

    today = datetime.now().strftime("%Y-%m-%d")
    soon_cutoff = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    # Loans are matched by borrower_name/contact since Loan isn't tied to
    # Student by foreign key (borrowing supports non-registered borrowers
    # too) -- match on this student's ID showing up in the contact field,
    # which is how the loan form auto-fills it during checkout.
    active_loans = Loan.query.filter(
        Loan.date_returned.is_(None),
        Loan.contact == student.student_id
    ).order_by(Loan.due_date).all()

    borrowed_count = len(active_loans)
    overdue_count = len([l for l in active_loans if l.due_date < today])
    due_soon_count = len([l for l in active_loans if today <= l.due_date <= soon_cutoff])

    return render_template(
        "portal.html",
        student=student,
        active_loans=active_loans,
        borrowed_count=borrowed_count,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        today=today
    )


@app.route("/portal/history")
def student_portal_history():
    student_id = session.get("student_portal_id")
    if not student_id:
        return redirect("/portal/login")

    student = Student.query.get(student_id)
    if student is None:
        session.pop("student_portal_id", None)
        return redirect("/portal/login")

    all_loans = Loan.query.filter(
        Loan.contact == student.student_id
    ).order_by(Loan.date.desc()).all()

    today = datetime.now().strftime("%Y-%m-%d")

    return render_template("portal_history.html", student=student, loans=all_loans, today=today)


@app.route("/portal/logout")
def portal_logout():
    session.pop("student_portal_id", None)
    return redirect("/portal/login")


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d"))


class LibrarySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opening_hours = db.Column(db.Text, default="Mon-Fri: 8:00am - 6:00pm\nSat: 9:00am - 2:00pm\nSun: Closed")
    contact_email = db.Column(db.String(150), default="library@sjbc.edu.gh")
    contact_phone = db.Column(db.String(50), default="")
    contact_address = db.Column(db.String(250), default="")


def get_settings():
    settings = LibrarySettings.query.first()
    if settings is None:
        settings = LibrarySettings()
        db.session.add(settings)
        db.session.commit()
    return settings


@app.route("/")
def home():
    settings = get_settings()
    featured = Book.query.filter_by(is_deleted=False, featured=True).limit(3).all()
    announcements = Announcement.query.order_by(Announcement.date.desc()).limit(3).all()
    return render_template("home.html", settings=settings, featured=featured, announcements=announcements)


@app.route("/catalogue")
def catalogue():
    search = request.args.get("search", "").strip()
    resource_type = request.args.get("type", "all")

    results = []
    if resource_type in ("all", "books"):
        query = Book.query.filter_by(is_deleted=False)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Book.title.ilike(like)) | (Book.author.ilike(like)) | (Book.isbn.ilike(like))
            )
        results = query.order_by(Book.title).all()

    active_counts = {}
    for loan in Loan.query.filter(Loan.date_returned.is_(None)).all():
        active_counts[loan.book_id] = active_counts.get(loan.book_id, 0) + 1

    available_map = {}
    for b in results:
        remaining = (b.copies or 0) - active_counts.get(b.id, 0)
        available_map[b.id] = remaining if remaining > 0 else 0

    return render_template(
        "catalogue.html",
        results=results,
        available_map=available_map,
        search=search,
        resource_type=resource_type
    )


@app.route("/coming-soon")
def coming_soon():
    feature = request.args.get("feature", "This feature")
    return render_template("coming_soon.html", feature=feature)


@app.route("/announcements/add", methods=["POST"])
@login_required
def add_announcement():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()

    if not title:
        flash("Announcement title is required.", "danger")
        return redirect("/dashboard")

    db.session.add(Announcement(title=title, body=body))
    db.session.commit()
    flash("Announcement posted.", "success")
    return redirect("/dashboard")


@app.route("/announcements/<int:id>/delete", methods=["POST"])
@login_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash("Announcement removed.", "success")
    return redirect("/dashboard")


@app.route("/settings/update", methods=["POST"])
@login_required
def update_settings():
    settings = get_settings()
    settings.opening_hours = request.form.get("opening_hours", "").strip()
    settings.contact_email = request.form.get("contact_email", "").strip()
    settings.contact_phone = request.form.get("contact_phone", "").strip()
    settings.contact_address = request.form.get("contact_address", "").strip()
    db.session.commit()
    flash("Library settings updated.", "success")
    return redirect("/dashboard")


@app.route("/books/<int:id>/toggle-featured", methods=["POST"])
@login_required
def toggle_featured(id):
    book = Book.query.get_or_404(id)
    book.featured = not book.featured
    db.session.commit()
    flash(f"'{book.title}' {'added to' if book.featured else 'removed from'} Featured Books.", "success")
    return redirect("/books")


# =========================
# LIBRARIAN DASHBOARD
# =========================
@app.route("/dashboard")
@login_required
def dashboard():
    today = datetime.now().strftime("%Y-%m-%d")

    todays_checkins = (
        CheckIn.query.filter(CheckIn.timestamp.like(f"{today}%"))
        .order_by(CheckIn.id.desc())
        .all()
    )

    active_loans = Loan.query.filter(Loan.date_returned.is_(None)).all()
    overdue_loans = [loan for loan in active_loans if loan.due_date < today]

    non_deleted_books = Book.query.filter_by(is_deleted=False).all()
    total_books = sum(b.copies or 0 for b in non_deleted_books)
    active_loans_for_existing_books = [l for l in active_loans if l.book and not l.book.is_deleted]
    available_books = total_books - len(active_loans_for_existing_books)

    return render_template(
        "index.html",
        todays_checkins=todays_checkins,
        active_loans=active_loans,
        overdue_count=len(overdue_loans),
        total_books=total_books,
        available_books=available_books,
        today=today,
        announcements=Announcement.query.order_by(Announcement.date.desc()).all(),
        settings=get_settings()
    )


# =========================
# STUDENT MANAGEMENT
# =========================
@app.route("/students/import", methods=["POST"])
@login_required
def import_students():
    file = request.files.get("csv_file")

    if not file or file.filename == "":
        flash("Please choose a CSV file to upload.", "danger")
        return redirect("/dashboard")

    if not file.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file.", "danger")
        return redirect("/dashboard")

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)

        added = 0
        skipped = 0
        valid_levels = {"100", "200", "300", "400"}

        for row in reader:
            student_id = (row.get("student_id") or "").strip()
            name = (row.get("name") or "").strip()
            course = (row.get("course") or "").strip()
            level = (row.get("level") or "").strip()

            if not student_id or not name:
                continue

            if level not in valid_levels:
                level = "100"

            if Student.query.filter_by(student_id=student_id).first():
                skipped += 1
                continue

            db.session.add(Student(student_id=student_id, name=name, course=course, level=level))
            added += 1

        db.session.commit()
        flash(f"Import complete: {added} student(s) added, {skipped} already existed and were skipped.", "success")

    except Exception:
        flash("Couldn't read that file. Make sure it's a CSV with 'student_id', 'name', 'course', and 'level' columns.", "danger")

    return redirect("/dashboard")


@app.route("/students/promote", methods=["POST"])
@login_required
def promote_students():
    valid_levels = {"100", "200", "300"}  # 400 is the ceiling -- no further promotion
    promoted = 0

    for student in Student.query.all():
        if student.level in valid_levels:
            student.level = str(int(student.level) + 100)
            promoted += 1

    db.session.commit()
    flash(f"Promoted {promoted} student(s) to their next level.", "success")
    return redirect("/dashboard")


@app.route("/students/add", methods=["POST"])
@login_required
def add_student():
    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    course = request.form.get("course", "").strip()
    level = request.form.get("level", "100").strip()

    if not student_id or not name:
        flash("Student ID and name are both required.", "danger")
        return redirect("/books")

    if level not in {"100", "200", "300", "400"}:
        level = "100"

    if Student.query.filter_by(student_id=student_id).first():
        flash("A student with that ID already exists.", "danger")
        return redirect("/books")

    student = Student(student_id=student_id, name=name, course=course, level=level)
    db.session.add(student)
    db.session.commit()

    flash(f"Student {name} registered.", "success")
    return redirect("/books")


# =========================
# BOOK CATALOG
# =========================
@app.route("/books")
@login_required
def books():
    search = request.args.get("search", "").strip()

    query = Book.query.filter_by(is_deleted=False)
    if search:
        like = f"%{search}%"
        query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)))

    all_books = query.order_by(Book.title).all()

    active_counts = {}
    for loan in Loan.query.filter(Loan.date_returned.is_(None)).all():
        active_counts[loan.book_id] = active_counts.get(loan.book_id, 0) + 1

    available_map = {}
    total_available = 0
    for b in all_books:
        remaining = (b.copies or 0) - active_counts.get(b.id, 0)
        if remaining < 0:
            remaining = 0
        available_map[b.id] = remaining
        total_available += remaining

    total_copies = sum(b.copies or 0 for b in all_books)

    return render_template(
        "books.html",
        books=all_books,
        search=search,
        available_count=total_available,
        total_copies=total_copies,
        available_map=available_map
    )


@app.route("/books/add", methods=["POST"])
@login_required
def add_book():
    date = request.form.get("date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    year = request.form.get("year", "").strip()
    isbn = request.form.get("isbn", "").strip()
    accession_no = request.form.get("accession_no", "").strip()
    acquisition_type = request.form.get("acquisition_type", "").strip()
    acquisition_other = request.form.get("acquisition_other", "").strip()
    remarks = request.form.get("remarks", "").strip()

    try:
        copies = int(request.form.get("copies", "1"))
    except ValueError:
        copies = 1
    if copies < 1:
        copies = 1

    if not title:
        flash("Book title is required.", "danger")
        return redirect("/books")

    if acquisition_type not in {"Purchased", "Donated", "Other"}:
        acquisition_type = "Other"

    book = Book(
        date=date,
        title=title,
        author=author,
        year=year,
        isbn=isbn,
        accession_no=accession_no,
        copies=copies,
        acquisition_type=acquisition_type,
        acquisition_other=acquisition_other if acquisition_type == "Other" else "",
        remarks=remarks,
        is_deleted=False
    )
    db.session.add(book)
    db.session.commit()

    flash(f"'{title}' added to the catalog.", "success")
    return redirect("/books")


@app.route("/books/<int:id>/delete", methods=["POST"])
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)

    book.is_deleted = True
    book.date_deleted = datetime.now().strftime("%Y-%m-%d")
    db.session.commit()

    flash(f"'{book.title}' moved to Deleted Books.", "success")
    return redirect("/books")


@app.route("/books/deleted")
@login_required
def deleted_books():
    removed = Book.query.filter_by(is_deleted=True).order_by(Book.date_deleted.desc()).all()
    return render_template("deleted_books.html", books=removed)


@app.route("/books/<int:id>/restore", methods=["POST"])
@login_required
def restore_book(id):
    book = Book.query.get_or_404(id)
    book.is_deleted = False
    book.date_deleted = None
    db.session.commit()
    flash(f"'{book.title}' restored to the catalog.", "success")
    return redirect("/books/deleted")


# =========================
# LOANS
# =========================
# =========================
# REPORTS
# =========================
@app.route("/reports")
@login_required
def reports():
    today = datetime.now().strftime("%Y-%m-%d")

    # Most borrowed books (all-time, by loan count)
    book_counts = {}
    for loan in Loan.query.all():
        book_counts[loan.book_id] = book_counts.get(loan.book_id, 0) + 1

    most_borrowed = []
    for book_id, count in sorted(book_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        book = Book.query.get(book_id)
        if book:
            most_borrowed.append((book, count))
    max_borrow_count = most_borrowed[0][1] if most_borrowed else 1

    # Busiest check-in days (all-time, by date)
    day_counts = {}
    for c in CheckIn.query.all():
        day = c.timestamp[:10]  # "YYYY-MM-DD" prefix of the stored timestamp
        day_counts[day] = day_counts.get(day, 0) + 1

    busiest_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:7]
    max_day_count = busiest_days[0][1] if busiest_days else 1

    # Overall totals
    total_borrowings = Loan.query.count()
    total_returns = Loan.query.filter(Loan.date_returned.isnot(None)).count()
    currently_overdue = Loan.query.filter(
        Loan.date_returned.is_(None), Loan.due_date < today
    ).count()
    total_students = Student.query.count()
    total_book_titles = Book.query.filter_by(is_deleted=False).count()
    total_checkins = CheckIn.query.count()

    return render_template(
        "reports.html",
        most_borrowed=most_borrowed,
        max_borrow_count=max_borrow_count,
        busiest_days=busiest_days,
        max_day_count=max_day_count,
        total_borrowings=total_borrowings,
        total_returns=total_returns,
        currently_overdue=currently_overdue,
        total_students=total_students,
        total_book_titles=total_book_titles,
        total_checkins=total_checkins
    )


@app.route("/reports/export")
@login_required
def export_loans():
    loans = Loan.query.order_by(Loan.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Borrower", "Level", "Book", "Copy #", "Contact",
        "Due Date", "Renewed", "Returned", "Remarks"
    ])

    for loan in loans:
        writer.writerow([
            loan.date, loan.borrower_name,
            loan.level_other if loan.level == "Other" else loan.level,
            loan.book.title if loan.book else "", loan.copy_number, loan.contact,
            loan.due_date, loan.renewal_date or "", loan.date_returned or "", loan.remarks or ""
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=loans_export.csv"}
    )


@app.route("/loans")
@login_required
def loans():
    today = datetime.now().strftime("%Y-%m-%d")
    active_loans = Loan.query.filter(Loan.date_returned.is_(None)).order_by(Loan.due_date).all()

    active_counts = {}
    for loan in active_loans:
        active_counts[loan.book_id] = active_counts.get(loan.book_id, 0) + 1

    available_books = []
    for b in Book.query.filter_by(is_deleted=False).order_by(Book.title).all():
        remaining = (b.copies or 0) - active_counts.get(b.id, 0)
        if remaining > 0:
            available_books.append((b, remaining))

    returned_loans = (
        Loan.query.filter(Loan.date_returned.isnot(None))
        .order_by(Loan.date_returned.desc())
        .limit(20)
        .all()
    )

    students = Student.query.order_by(Student.name).all()
    students_json = json.dumps([
        {"name": s.name, "student_id": s.student_id, "level": s.level}
        for s in students
    ])

    return render_template(
        "loans.html",
        loans=active_loans,
        today=today,
        available_books=available_books,
        loaned_count=len(active_loans),
        returned_loans=returned_loans,
        students=students,
        students_json=students_json
    )


@app.route("/loans/add", methods=["POST"])
@login_required
def add_loan():
    date = request.form.get("date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    borrower_name = request.form.get("borrower_name", "").strip()
    level = request.form.get("level", "").strip()
    level_other = request.form.get("level_other", "").strip()
    copy_number = request.form.get("copy_number", "").strip()
    book_id = request.form.get("book_id", "")
    contact = request.form.get("contact", "").strip()

    if not borrower_name or not book_id:
        flash("Borrower name and book are required.", "danger")
        return redirect("/loans")

    book = Book.query.get(int(book_id)) if book_id.isdigit() else None
    if book is None or book.is_deleted:
        flash("Please select a valid book.", "danger")
        return redirect("/loans")

    active_count = Loan.query.filter_by(book_id=book.id, date_returned=None).count()
    if active_count >= (book.copies or 0):
        flash("No copies of that book are currently available.", "danger")
        return redirect("/loans")

    if copy_number:
        try:
            copy_num_int = int(copy_number)
        except ValueError:
            flash("Copy number must be a number.", "danger")
            return redirect("/loans")

        if copy_num_int < 1 or copy_num_int > (book.copies or 0):
            flash(f"'{book.title}' only has {book.copies} cop{'y' if book.copies == 1 else 'ies'} -- copy number {copy_num_int} doesn't exist.", "danger")
            return redirect("/loans")

        already_out = Loan.query.filter_by(
            book_id=book.id, copy_number=copy_number, date_returned=None
        ).first()
        if already_out:
            flash(f"Copy {copy_num_int} of '{book.title}' is already on loan.", "danger")
            return redirect("/loans")

    valid_levels = {"100", "200", "300", "400", "Other"}
    if level not in valid_levels:
        level = "Other"

    try:
        loan_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        loan_date = datetime.now()

    # Students (100-400 level) get a 2-week loan period. Anyone else
    # ("Other" -- staff, community members, etc.) gets 30 days.
    loan_days = 14 if level != "Other" else 30
    due_date = (loan_date + timedelta(days=loan_days)).strftime("%Y-%m-%d")

    loan = Loan(
        date=date,
        borrower_name=borrower_name,
        level=level,
        level_other=level_other if level == "Other" else "",
        copy_number=copy_number,
        book_id=book.id,
        contact=contact,
        due_date=due_date
    )
    db.session.add(loan)
    db.session.commit()

    flash(f"'{book.title}' loaned out to {borrower_name}, due {due_date}.", "success")
    return redirect("/loans")


@app.route("/loans/<int:id>/renew", methods=["POST"])
@login_required
def renew_loan(id):
    loan = Loan.query.get_or_404(id)

    if loan.date_returned:
        flash("Can't renew a loan that's already been returned.", "danger")
        return redirect("/loans")

    duration_choice = request.form.get("duration", "14")
    days = 30 if duration_choice == "30" else 14
    new_due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    loan.due_date = new_due_date
    loan.renewal_date = datetime.now().strftime("%Y-%m-%d")
    db.session.commit()

    flash(f"Loan renewed -- new due date {new_due_date}.", "success")
    return redirect("/loans")


@app.route("/loans/<int:id>/return", methods=["POST"])
@login_required
def return_loan(id):
    loan = Loan.query.get_or_404(id)

    if loan.date_returned:
        flash("This loan was already marked returned.", "danger")
        return redirect("/loans")

    loan.date_returned = datetime.now().strftime("%Y-%m-%d")
    loan.remarks = request.form.get("remarks", "").strip()
    db.session.commit()

    flash(f"'{loan.book.title}' marked as returned.", "success")
    return redirect("/loans")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)