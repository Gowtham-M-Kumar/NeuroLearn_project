# NEURO Learning Platform - Authentication Credentials

## Superuser Account
**Email:** admin@neurolearn.com  
**Username:** admin  
**Password:** NeuroLearn2024!  
**Role:** Parent (with admin privileges)  
**Access:** Full admin access to Django admin and all platform features

---

## Test User Accounts (To be created)

### Parent Test Account
**Email:** parent@neurolearn.com  
**Password:** Parent123!  
**Role:** Parent  
**Purpose:** Test parent dashboard and child management features

### Therapist Test Account
**Email:** therapist@neurolearn.com  
**Password:** Therapist123!  
**Role:** Therapist  
**Purpose:** Test therapist dashboard and patient management features

### Teacher Test Account
**Email:** teacher@neurolearn.com  
**Password:** Teacher123!  
**Role:** Teacher  
**Purpose:** Test teacher dashboard and classroom management features

### Child Test Account
**Email:** child@neurolearn.com  
**Password:** Child123!  
**Role:** Child  
**Purpose:** Test child dashboard and learning activities

---

## Access URLs

### Main Application
- **Login Page:** http://localhost:8000/login/
- **Registration Page:** http://localhost:8000/register/
- **Dashboard:** http://localhost:8000/dashboard/ (after login)
- **Profile:** http://localhost:8000/profile/ (after login)

### Admin Interface
- **Django Admin:** http://localhost:8000/admin/
- **User Management:** http://localhost:8000/users/ (admin only)

---

## Role-Based Features

### Parent Role
- View children's progress
- Monitor learning activities
- Communicate with therapists/teachers
- Access progress reports

### Therapist Role
- Manage patient profiles
- Create therapy routines
- Assign therapy activities
- Track patient progress

### Teacher Role
- Manage classroom activities
- Assign learning tasks
- Track student progress
- Communicate with parents

### Child Role
- Access assigned routines
- Play learning games
- Use drawing tools
- View progress

---

## Security Notes
- All passwords should be changed in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regular security audits recommended

---

## Development Setup
1. Activate virtual environment: `venv\Scripts\activate`
2. Run migrations: `python manage.py migrate`
3. Start server: `python manage.py runserver`
4. Access application at: http://localhost:8000

---

## Database Information
- **Database Type:** SQLite (development)
- **Database File:** db.sqlite3
- **Custom User Model:** apps.users.models.CustomUser
- **Profile Models:** ParentProfile, TherapistProfile, TeacherProfile, ChildProfile 