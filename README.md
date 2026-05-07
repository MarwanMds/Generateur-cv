# 📄 CV Generator

A full-featured web application that lets users create, customize, and export professional CVs using multiple templates — built with Django.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.x-green?logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap&logoColor=white)
![ReportLab](https://img.shields.io/badge/PDF-ReportLab-red)

---

## ✨ Features

### 👤 User Management
- Registration, login, and logout via Django Authentication
- User profile with photo upload
- Each user can create and manage multiple CVs

### 📝 Multi-Step CV Builder
| Step | Content |
|------|---------|
| 1 | Personal info, photo, social links, customization |
| 2 | Education history |
| 3 | Work experience |
| 4 | Skills, languages, interests |
| 5 | Review & export |

### 🎨 Customization
- **3 templates** — Modern (sidebar), Classic (traditional), Minimal (accent bar)
- Custom **primary and secondary colors** via color pickers
- Choose **font family and font size**
- Per-field typography styling (font, size, color per field)
- **Live preview** panel updates as you type on every step

### 📤 Export
- **PDF export** via ReportLab — each template renders a pixel-accurate PDF
- Profile photo rendered as a circular crop in the Modern template PDF
- Print-ready A4 format

### 🛡️ Admin Panel
- Custom role-based admin dashboard (separate from Django's built-in `/admin`)
- Manage users: view, delete, toggle staff status
- Manage CVs: list all CVs, preview any user's CV, delete
- Site statistics overview

### 💾 Autosave
- Forms autosave every 1.5 seconds while typing
- Toast indicator shows saving / saved / error status

---

## 🖥️ Screenshots

> Modern Template — Live Preview & PDF export match exactly

| Step 1 — Personal Info | Step 5 — Review |
|---|---|
| Live preview updates in real time | Full CV rendered with all sections |

---

## 🗂️ Project Structure

```
cv_generator/
├── accounts/          # Registration, login, user profile
├── admin_panel/       # Custom admin dashboard (not Django admin)
├── core/              # Home page
├── cv/                # CV models, multi-step forms, views, autosave
├── dashboard/         # User dashboard — list and manage CVs
├── export/            # PDF generation (ReportLab, 3 templates)
├── cv_generator/      # Project settings and root URLs
├── templates/         # All HTML templates (Bootstrap 5)
│   ├── base.html
│   ├── accounts/
│   ├── admin_panel/
│   ├── cv/
│   │   ├── step_base.html
│   │   ├── step1_personal.html
│   │   ├── step2_education.html
│   │   ├── step3_experience.html
│   │   ├── step4_skills.html
│   │   ├── step5_review.html
│   │   └── partials/
│   │       └── live_preview.html
│   └── dashboard/
├── static/
│   ├── css/
│   └── js/
│       ├── cv_preview.js     # Live preview engine (all 5 steps)
│       └── field_styler.js   # Per-field typography popovers
└── media/                    # Uploaded profile photos
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django (MVT architecture) |
| Database | MySQL 8.0 |
| Frontend | Django Templates + Bootstrap 5 |
| Interactivity | Vanilla JavaScript (no frameworks) |
| PDF Generation | ReportLab |
| Auth | Django built-in authentication |
| Forms | Django Forms + django-widget-tweaks |

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/your-username/cv-generator.git
cd cv-generator
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL database

```sql
CREATE DATABASE cv_generator_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cv_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cv_generator_db.* TO 'cv_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure settings

Open `cv_generator/settings.py` and update the database section:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cv_generator_db',
        'USER': 'cv_user',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

Also set a secure secret key:

```python
SECRET_KEY = 'your-secret-key-here'
```

### 6. Apply migrations

```bash
cd cv_generator
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Collect static files (production only)

```bash
python manage.py collectstatic
```

### 9. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000**

---

## 📦 Requirements

```
Django>=4.2
mysqlclient>=2.1
reportlab>=4.0
django-widget-tweaks>=1.5
Pillow>=10.0
```

Create a `requirements.txt` with:

```bash
pip freeze > requirements.txt
```

---

## 🗃️ Database Models

```
User (Django built-in)
 └── CV
      ├── Education      (degree, institution, dates)
      ├── Experience     (position, company, dates, description)
      ├── Skill          (name, category, proficiency)
      ├── Language       (name, level)
      └── Interest       (name)
```

Each CV stores:
- Personal info (name, email, phone, city, country, links)
- Design settings (template, primary color, secondary color, font)
- Per-field typography as a JSON field (`field_styles`)

---

## 🔐 Security

- CSRF protection on all forms (Django default)
- Password hashing (PBKDF2 + SHA256, Django default)
- Login required on all private views (`@login_required`)
- Admin panel protected by `@admin_required` decorator
- Input validation via Django Forms on every step
- Ownership check — users can only access their own CVs

---

## 🧭 URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | `core:home` | Landing page |
| `/accounts/register/` | `accounts:register` | User registration |
| `/accounts/login/` | `accounts:login` | Login |
| `/dashboard/` | `dashboard:index` | User's CV list |
| `/cv/new/` | `cv:new` | Create a new CV |
| `/cv/<pk>/step/<step>/` | `cv:step` | Multi-step form |
| `/cv/<pk>/export/pdf/` | `export:pdf` | Download CV as PDF |
| `/admin-panel/` | `admin_panel:overview` | Admin dashboard |
| `/admin/` | Django admin | Built-in admin |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Built by **Marwan MERDAS**

[![GitHub](https://img.shields.io/badge/GitHub-@marwan-black?logo=github)](https://github.com/your-username)