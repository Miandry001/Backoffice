# Back Office - Google Sheets Management System

A full-stack Python application for managing Google Sheets data with role-based access control, user management, and a customizable data entry interface.

## Security Features

- **Password Complexity Requirements**: Enforces strong passwords (8+ chars, uppercase, lowercase, digit, special character)
- **Role-Based Access Control**: Three-tier permission system (Admin, Supervisor, Agent)
- **Rate Limiting**: Prevents brute force attacks on authentication endpoints
- **Session Security**: HTTPONLY, SAMESITE, and SECURE flags for session cookies
- **CORS Protection**: Restricted to specific frontend domain
- **Input Validation**: All user inputs validated before processing
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Role Escalation Prevention**: Registration always defaults to 'agent' role
- **Self-Protection**: Admins cannot delete or deactivate themselves

## Features

- **Authentication System**: Login portal with role-based access (Admin, Supervisor, Agent)
- **User Management**: Admin panel to add, edit, and delete users
- **Google Sheets Integration**: Connect and manage Google Sheets with 8 sheets
  - Sheet 1: Main data entry sheet (accessible by all users)
  - Sheets 2-8: Reference sheets (admin/supervisor only)
- **Data Entry Interface**: 6-section column grouping for 73 columns
  - Real-time section switching without page refresh
  - Each section contains ~12 columns for better organization
  - **FIXED**: Proper column letter calculation for 73+ columns
- **Feature Toggles**: Admin can enable/disable features with one click
- **Customizable Sections**: Admin can modify column groupings via admin panel

## Tech Stack

### Backend
- Flask (Python web framework)
- Flask-SQLAlchemy (Database ORM)
- Flask-Login (Authentication)
- Google Sheets API (Data integration)
- SQLite (Database)

### Frontend
- React 18
- React Router
- TailwindCSS (Styling)
- Lucide React (Icons)
- Vite (Build tool)

## Project Structure

```
PythonProject/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication endpoints
│   ├── admin.py            # Admin panel endpoints
│   ├── sheets.py           # Google Sheets integration
│   ├── data.py             # Data management endpoints
│   └── init_db.py          # Database initialization script
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AdminPanel.jsx
│   │   │   ├── DataEntry.jsx
│   │   │   └── Navbar.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud Project with Sheets API enabled
- Google Service Account credentials (JSON file)

### Backend Setup

1. Navigate to the project directory:
```bash
cd C:/Users/Users/PycharmProjects/PythonProject
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
copy .env.example .env
```

Edit `.env` and add your settings:
```
FLASK_SECRET_KEY=your-secret-key-here
FLASK_APP=backend/app.py
FLASK_ENV=development
DATABASE_URL=sqlite:///backoffice.db
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
```

5. Place your Google Service Account credentials as `credentials.json` in the project root.

6. Initialize the database:
```bash
python backend/init_db.py
```

This creates:
- Default admin user (username: `admin`, password: `Admin@1234`)
- 6 default sections for 73 columns

**SECURITY WARNING**: Change the default admin password immediately after first login!

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

## Running the Application

### Start Backend
```bash
cd C:/Users/Users/PycharmProjects/PythonProject
.venv\Scripts\activate
python backend/app.py
```

Backend runs on `http://localhost:5000`

### Start Frontend
```bash
cd frontend
npm run dev
```

Frontend runs on `http://localhost:3000`

## Usage

### 1. Login
- access the application at `http://localhost:3000`
- Default admin credentials:
  - Username: `admin`
  - Password: `Admin@1234`

**IMPORTANT**: Change the default password immediately after first login!

### 2. Connect Google Sheet
- Go to Admin Panel → Sheets tab
- Paste your Google Sheet URL
- Click "Connect"
- Share the sheet with your service account email

### 3. Manage Users (Admin only)
- Go to Admin Panel → Users tab
- Add new users with roles (admin, supervisor, agent)
- Edit or deactivate existing users

### 4. Configure Features (Admin only)
- Go to Admin Panel → Features tab
- Add new features
- Toggle features on/off with one click

### 5. Configure Sections (Admin only)
- Go to Admin Panel → Sections tab
- Modify column groupings
- Change section order and names

### 6. Data Entry
- Go to Data Entry page
- Connect a Google Sheet (if not already connected)
- Navigate between 6 sections using tabs
- Fill data in each section
- Click "Save Data" to append to Google Sheet

### 7. Access Reference Sheets (Admin/Supervisor only)
- Admin and supervisors can access and edit sheets 2-8
- Agents can only access and edit sheet 1 (main data sheet)

## Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download credentials JSON file
5. Share your Google Sheet with the service account email
6. Place credentials.json in the project root

## Role Permissions

| Action | Admin | Supervisor | Agent |
|--------|-------|-----------|-------|
| Login | ✓ | ✓ | ✓ |
| View Dashboard | ✓ | ✓ | ✓ |
| Data Entry (Sheet 1) | ✓ | ✓ | ✓ |
| Data Entry (Sheets 2-8) | ✓ | ✓ | ✗ |
| Manage Users | ✓ | ✗ | ✗ |
| Manage Features | ✓ | ✗ | ✗ |
| Manage Sections | ✓ | ✗ | ✗ |
| Connect Sheets | ✓ | ✓ | ✗ |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Admin
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Delete user
- `GET /api/admin/features` - List features
- `POST /api/admin/features` - Create feature
- `POST /api/admin/features/:id/toggle` - Toggle feature
- `DELETE /api/admin/features/:id` - Delete feature
- `GET /api/admin/sections` - List sections
- `POST /api/admin/sections` - Create section
- `PUT /api/admin/sections/:id` - Update section
- `DELETE /api/admin/sections/:id` - Delete section

### Sheets
- `POST /api/sheets/connect` - Connect Google Sheet
- `GET /api/sheets/list` - List connected sheets
- `GET /api/sheets/:id/metadata` - Get sheet metadata
- `GET /api/sheets/:id/data` - Get sheet data
- `POST /api/sheets/:id/data` - Update sheet data
- `POST /api/sheets/:id/append` - Append data to sheet

### Data
- `GET /api/data/sections` - Get column sections
- `GET /api/data/records` - Get data records
- `POST /api/data/records` - Create record
- `PUT /api/data/records/:id` - Update record
- `DELETE /api/data/records/:id` - Delete record

## Security Notes

- **Change the default admin password immediately after first login**
- Keep your Google Service Account credentials secure
- Use environment variables for sensitive configuration
- Enable HTTPS in production (set `SESSION_COOKIE_SECURE=True`)
- Use Redis for rate limiting storage in production
- Update `FRONTEND_URL` to your production domain
- Generate a strong `FLASK_SECRET_KEY` for production
- Regularly update dependencies
- Enable database backups
- Monitor logs for suspicious activity

## Security Fixes Applied

### Critical Security Vulnerabilities Fixed:
1. **Role Escalation Prevention**: Registration now always defaults to 'agent' role
2. **Password Complexity**: Enforced strong password requirements
3. **Rate Limiting**: Added Flask-Limiter to prevent brute force attacks
4. **CORS Restriction**: Limited to specific frontend domain
5. **Session Security**: Added HTTPONLY, SAMESITE, and SECURE flags
6. **Input Validation**: All inputs validated before processing
7. **Self-Protection**: Admins cannot delete/deactivate themselves

### Critical Algorithm Bugs Fixed:
1. **Column Letter Calculation**: Fixed bug that failed beyond 26 columns (Z)
   - Old: `chr(64 + n)` only worked for columns 1-26
   - New: Proper Excel-style notation handles any number of columns
   - Example: 73 columns now correctly maps to column BA
2. **Range Limitation**: Updated range from `A1:ZZ` to `A1:BA` for 73 columns

### Best Practices Implemented:
1. Comprehensive code comments for maintainability
2. Database transactions with rollback on error
3. Generic error messages to prevent user enumeration
4. Email validation with regex
5. Pagination limits to prevent excessive data retrieval
6. Service instance caching for Google Sheets API
7. Proper error handling without exposing sensitive information

## Troubleshooting

### Google Sheets API Errors
- Ensure the sheet is shared with your service account email
- Verify the credentials.json file is correctly placed
- Check that the Sheets API is enabled in your Google Cloud project
- Verify the sheet ID format (should match regex: `[a-zA-Z0-9-_]{10,50}`)

### Database Issues
- Delete `backoffice.db` and run `python backend/init_db.py` to reset
- Ensure SQLite is properly installed
- Check database file permissions

### Authentication Issues
- Verify password meets complexity requirements (8+ chars, uppercase, lowercase, digit, special)
- Check that user account is active
- Verify session cookie settings
- Clear browser cookies if session issues persist

### Frontend Build Issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check that Node.js version is 16 or higher
- Verify CORS settings match frontend URL

### Rate Limiting Issues
- If rate limit errors occur, wait before retrying
- Adjust rate limits in config.py if needed
- Use Redis for distributed rate limiting in production

## License

This project is provided as-is for educational and commercial use.
