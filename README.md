# Library Management System

A web-based library management system built with Python and Flask to simplify library operations and improve access to library resources.

The system provides librarians with tools to manage books, students, borrowing activities, check-ins, reports, and digital resources. It also provides students and visitors with a public catalogue, a check-in kiosk, and a student portal where they can view their borrowing activities.

## Features

### Librarian Management
- Dashboard with library activity summaries.
- Book catalogue management and availability tracking.
- Book borrowing, renewals, and returns.
- Automatic borrowing due dates.
- Student registration and bulk CSV import.
- Student level promotion.
- Loan history and library reports.
- CSV export of loan records.
- Announcements and library settings.
- Digital resource management.
- Deleted book recovery.

### Student and Visitor Features
- Public library homepage.
- Searchable book catalogue.
- Real-time book availability.
- Library check-in kiosk.
- Student portal with borrowing history.
- Current, due-soon, and overdue loan information.
- Access to digital resources.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Web application framework |
| Flask-SQLAlchemy | Database management |
| Flask-Login | User authentication |
| Flask-WTF | Form handling and CSRF protection |
| Flask-Limiter | Rate limiting |
| PostgreSQL / SQLite | Database |
| Gunicorn | Production application server |
| Render | Application hosting |

## Getting Started

### Prerequisites
- Python 3
- Git
- pip

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Deadfreeze72/Library-CheckIn-System.git
cd Library-CheckIn-System
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

**3. Activate the environment**

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source venv/bin/activate
```

**4. Install dependencies**

If the project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**5. Configure environment variables**

Create a `.env` file in the project directory and configure the required variables.

```env
SECRET_KEY=your-secure-secret-key
FLASK_DEBUG=0
DATABASE_URL=your-database-url
```

Use the database configuration appropriate for your environment. Do not commit your `.env` file or expose database credentials.

**6. Start the application**

```bash
python app.py
```

Open your browser and visit:

`http://127.0.0.1:5000`

## Student CSV Import

Librarians can import student records using a CSV file with the following column headers:

```csv
student_id,name,course,level
```

- `student_id` and `name` are required.
- Supported student levels include 100, 200, 300, and 400.
- Existing student IDs are skipped during import.

## Main Application Pages

| Page | URL | Access |
|---|---|---|
| Home | `/` | Public |
| Catalogue | `/catalogue` | Public |
| Digital Resources | `/resources` | Public |
| Check-in Kiosk | `/checkin` | Public |
| Student Portal | `/portal` | Student |
| Librarian Login | `/login` | Public |
| Dashboard | `/dashboard` | Librarian |
| Books | `/books` | Librarian |
| Loans | `/loans` | Librarian |
| Reports | `/reports` | Librarian |
| Manage Resources | `/resources/admin` | Librarian |

## Deployment

The application can be deployed using Render.

A production deployment requires:
- A configured production database.
- Environment variables, including a secure `SECRET_KEY`.
- A production application server such as Gunicorn.
- Persistent storage for uploaded files, or an appropriate external file-storage service.

## Security

The application includes security measures such as:
- Password hashing.
- CSRF protection.
- Rate limiting on selected routes.
- File upload restrictions and filename sanitization.

Sensitive configuration files, database credentials, and private user data should never be committed to the repository.

## Project Structure

```text
Library-CheckIn-System/
├── app.py
├── templates/
├── static/
├── uploads/
├── requirements.txt
├── .gitignore
└── README.md
```

*Actual project structure may include additional files and directories.*

## Author

**Caesar Weyipe Awariwe**

GitHub: https://github.com/Deadfreeze72