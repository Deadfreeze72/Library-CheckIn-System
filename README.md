# Library Management System

A web-based library management system built with **Flask**. It lets librarians manage the book catalogue, loans, students, and digital resources, while students and visitors can search the catalogue, check in at a kiosk, and view their own borrowing activity.

## Features

### For librarians (login required)
- **Dashboard** with today's check-ins, active loans, overdue count, and book availability
- **Book catalogue management**: add books with ISBN, accession number, copies, and acquisition type (Purchased / Donated / Other)
- **Soft delete and restore**: deleted books move to a "Deleted Books" list and can be restored
- **Featured books**: highlight selected books on the home page
- **Loan management**: check books out, renew loans, and mark them returned
- **Automatic due dates**: 14 days for students (levels 100-400), 30 days for other borrowers
- **Copy tracking**: prevents loaning more copies than exist or the same copy twice
- **Student management**: register students one by one or bulk import from CSV
- **Level promotion**: promote all students to their next level in one click
- **Reports**: most borrowed books, busiest check-in days, and overall totals
- **CSV export** of the full loan history
- **Announcements** and editable **library settings** (opening hours and contact details)
- **Digital resources**: upload files or add links to e-books, journals, and research papers

### For students and visitors (no librarian login)
- **Home page** with featured books, announcements, and opening hours
- **Public catalogue** with search by title, author, or ISBN and live availability
- **Check-in kiosk** where students check in with their student ID or name
- **Student portal** showing current loans, due-soon and overdue counts, and borrowing history
- **Digital resources** browsing and downloading

## Tech Stack

- Python 3 and Flask
- Flask-SQLAlchemy (SQLite by default)
- Flask-Login (librarian authentication)
- Flask-WTF (CSRF protection)
- Flask-Limiter (rate limiting)
- python-dotenv (environment variables)
- Werkzeug (password hashing and secure file uploads)

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install flask flask-sqlalchemy flask-login flask-wtf flask-limiter python-dotenv
```

### 4. Configure environment variables

Create a file named `.env` in the project folder:

```
SECRET_KEY=replace-this-with-a-long-random-string
FLASK_DEBUG=0
# Optional: use a different database instead of the default SQLite file
# DATABASE_URL=sqlite:///library.db
```

If `SECRET_KEY` is not set, a random key is generated each time the app starts, which logs everyone out on restart. Always set one.

### 5. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The database and tables are created automatically on first run.

### 6. Create the first librarian account

Go to **/register**, create an account, then sign in at **/login**.

## Importing Students from CSV

From the dashboard, upload a `.csv` file with these column headers:

```
student_id,name,course,level
```

- `student_id` and `name` are required
- `level` should be `100`, `200`, `300`, or `400` (anything else defaults to `100`)
- Students whose ID already exists are skipped

## Main Pages

| Page | URL | Access |
|------|-----|--------|
| Home | `/` | Public |
| Catalogue | `/catalogue` | Public |
| Digital resources | `/resources` | Public |
| Check-in kiosk | `/checkin` | Public |
| Student portal | `/portal` | Student ID or name |
| Librarian login | `/login` | Public |
| Dashboard | `/dashboard` | Librarian |
| Books | `/books` | Librarian |
| Loans | `/loans` | Librarian |
| Reports | `/reports` | Librarian |
| Manage resources | `/resources/admin` | Librarian |

## Project Structure

```
.
├── app.py            # Flask application: routes, models, configuration
├── templates/        # HTML templates
├── static/           # CSS, images, and other static files
├── uploads/          # Uploaded digital resources (created automatically)
├── library.db        # SQLite database (created automatically)
└── .env              # Environment variables (not committed)
```

## Security Notes

- Passwords are hashed with Werkzeug
- All forms are protected with CSRF tokens
- Login, registration, and check-in routes are rate limited
- Uploads are restricted to approved file types and filenames are sanitized
- Keep `.env`, `library.db`, and `uploads/` out of Git by listing them in `.gitignore`

## Author

Built by **Caesar Weyipe Awariwe**.