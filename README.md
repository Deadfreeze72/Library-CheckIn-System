# St. John Bosco College of Education — Library System

A web-based library management system for a teacher-training college. It combines a public library website, a student self-service account, a librarian dashboard, and a staff area where lecturers can contribute their own publications for the librarian to approve.

**Live demo:** https://library-checkin-system.onrender.com

> The free hosting plan puts the site to sleep when nobody has visited for a while, so the first page load can take up to a minute.

<!--
SCREENSHOTS: save your screenshots in a folder called docs/screenshots/ with these
names, then delete this comment's opening and closing markers to show them.

| Public homepage | Librarian dashboard |
|---|---|
| ![Homepage](docs/screenshots/home.png) | ![Dashboard](docs/screenshots/dashboard.png) |

| Loans | Student account |
|---|---|
| ![Loans](docs/screenshots/loans.png) | ![Student account](docs/screenshots/student-account.png) |
-->

## What it does

### For the public and students
- **Homepage** with a catalogue search, quick-access tiles, featured books, library news, opening hours and contact details.
- **Catalogue search** by title, author or ISBN, showing how many copies are available right now.
- **E-Resources:** browse and search E-Books, Journals and Staff Publications. Each opens as a file or an external link.
- **Student check-in page:** a student types their Student ID or name and is logged in as present, with name suggestions as they type.
- **My Student Account:** a student enters their Student ID to see what they've borrowed, what is due soon, what is overdue, and their full borrowing history.

### For the librarian
- **Dashboard:** today's check-ins, active loans, overdue count and book availability at a glance.
- **Books:** add books with date, title, author/editor, year, ISBN, accession number, number of copies, whether purchased or donated, and remarks. Search the catalogue, feature books on the homepage, and delete safely: removed books go to a *Deleted Books* list and can be restored.
- **Loans:**
  - Type a student's name and their level and Student ID fill in automatically.
  - The copy number is checked against the number of copies the book actually has, and the same copy can't be lent out twice.
  - The due date is set automatically: **2 weeks** for levels 100–400 and **30 days** for everyone else.
  - Renew for 2 weeks or 30 days, and record remarks when a book comes back.
- **Students:** register one at a time or import a whole year group from a CSV file. A *New Academic Year* button moves every student up a level (up to 400).
- **Reports:** totals, most borrowed books, busiest check-in days, and a CSV export of every loan.
- **Site content:** post library news and edit the opening hours and contact details shown on the homepage.
- **E-Resources:** add items by uploading a file or pasting a link, and review staff submissions before they go public.
- **Staff accounts:** create staff logins, reset their passwords, and remove them.

### For staff (lecturers)
- Log in to a page of their own and submit an E-Book, Journal or Staff Publication as a file or a link.
- Submissions stay **hidden until the librarian approves them**. Staff can see each one's status and remove their own.
- Staff can change their own password and cannot open any librarian page.

## Who can do what

| | Public | Student | Staff | Librarian |
|---|:--:|:--:|:--:|:--:|
| Search catalogue and browse approved E-Resources | ✅ | ✅ | ✅ | ✅ |
| Check in at the library | ✅ | ✅ | | |
| See own borrowed books and history | | ✅ | | |
| Submit resources (pending approval) | | | ✅ | |
| Approve, add and delete resources | | | | ✅ |
| Manage books, loans, students, reports, news, settings | | | | ✅ |
| Create staff accounts and reset their passwords | | | | ✅ |

## Built with

- **Python** and **Flask**, with Flask-SQLAlchemy, Flask-Login, Flask-WTF and Flask-Limiter
- **PostgreSQL** (Neon) in production, **SQLite** for local development
- **Jinja2** templates, plain **CSS** and a little JavaScript, with [Lucide](https://lucide.dev) icons
- **Gunicorn** on **Render** for hosting
- **Brevo** for password-reset emails (optional)

## Run it on your own computer

You need Python 3 installed. The project was developed and tested on Python 3.12–3.14.

```bash
git clone https://github.com/Deadfreeze72/Library-CheckIn-System.git
cd Library-CheckIn-System

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Open `.env` and set `SECRET_KEY`. You can generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then start the app:

```bash
python app.py
```

Visit http://127.0.0.1:5000. The **first account you register becomes the librarian**. After that, registration closes and the librarian creates any other accounts from the **Staff** page.

With no `DATABASE_URL` set, the app uses a local SQLite file (`library.db`) that it creates by itself.

## Settings (environment variables)

| Variable | Required | What it does |
|---|:--:|---|
| `SECRET_KEY` | Yes | Signs login sessions and password-reset links. Keep it private and use a long random value. |
| `DATABASE_URL` | In production | PostgreSQL connection string. If missing, the app falls back to local SQLite. |
| `FLASK_DEBUG` | No | `1` turns on debug mode locally. Leave it `0` in production. |
| `BREVO_API_KEY` | No | Turns on "Forgot your password?" emails. |
| `MAIL_FROM` | With Brevo | The sender address, verified in your Brevo account. |
| `MAIL_FROM_NAME` | No | Sender name shown in the email. |

Without the email settings, everything else still works. Staff can ask the librarian to reset their password.

## Student CSV format

The bulk import on the dashboard expects a `.csv` file whose first row is exactly:

```csv
student_id,name,course,level
STU2024001,Ama Mensah,Early Childhood Education,100
STU2024002,Kwame Boateng,Mathematics Education,200
```

- `level` must be `100`, `200`, `300` or `400`. Anything else is treated as `100`.
- A student whose ID already exists is skipped, so re-uploading an updated list is safe.
- From Excel, save as **CSV UTF-8 (Comma delimited)**. A ready-made example is in `students_template.csv`.

## Deploying (Render + Neon)

1. Create a free PostgreSQL project on [Neon](https://neon.tech) and copy its connection string.
2. Create a **Web Service** on [Render](https://render.com) connected to this repository.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Under **Environment**, add `SECRET_KEY` and `DATABASE_URL` (and the Brevo settings if you want password-reset emails).
4. Deploy. The tables are created automatically on first start. When a later version adds new columns, the app adds them to the existing database by itself on startup. It never deletes or alters existing data.

Render's free plan blocks ordinary outgoing email and wipes its disk on restart. That is why password-reset emails go through Brevo's web API, and why uploaded documents are stored in the database rather than on disk.

## Project layout

```
app.py                  Routes, database models and all application logic
requirements.txt        Python dependencies
.env.example            Template for your settings
students_template.csv   Example file for the bulk student import
templates/              Pages (public site, librarian, student, staff)
static/style.css        Styling, including the phone layout
static/images/          School crest and favicon
```

## Security notes

- Passwords are hashed, never stored as plain text.
- Every form is protected against cross-site request forgery.
- Sign-in, check-in and password-reset pages are rate-limited, and there is a sitewide per-visitor limit.
- Librarian-only pages are blocked for staff at the server, not just hidden from the menu.
- Open registration ends once the first (librarian) account exists, so strangers can't sign themselves up.
- Staff on a temporary password must choose their own before doing anything else.
- Password-reset links expire after one hour and work only once. The site gives the same answer whether or not an email is registered, so it can't be used to find out who has an account.
- Uploads are limited to PDF, Word, PowerPoint, EPUB and text files up to 15 MB. External links must start with `http://` or `https://`.
- Secrets come from environment variables and are never committed. `.env` is git-ignored.

## Design decisions and limitations

- **The student account has no password.** A student enters their Student ID and sees only their own loans and due dates. This was a deliberate choice for low-sensitivity information. A PIN could be added.
- **Loans appear in a student's account by Student ID.** A loan recorded without the ID filled in won't show there. Choosing the student's name from the suggestions fills it in automatically.
- **Uploaded documents live in the database.** The free Neon plan holds about 500 MB, shared with everything else, and the dashboard shows how much is used. Larger items can be added as links.
- **Rate-limit counters are kept in memory** and reset when the server restarts.
- **Icons and fonts load from the internet** (CDNs), so a connection is needed to see them.
- Not built: book reservations and overdue fines. Fines were left out because the library doesn't charge them.
- No automated test suite is included yet.

## Ideas for next

- Overdue reminders sent by email
- Book cover pictures on the homepage
- Moving documents to dedicated file storage if the library outgrows the free database
- A separate institutional repository for theses and research outputs
- Automated tests

## About

Built by Caesar Weyipe Awariwe, with requirements gathered from conversations with the college's librarian. The project was developed with AI assistance (Claude), and I tested, reviewed and deployed it myself.