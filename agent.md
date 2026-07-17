# Project Context: English Question Bank System

## What This Is
A Django web application for English language schools. Teachers log in and generate automatic exams from a question bank. No public API, no mobile app — web only.

---

## Current Status
> **Update this section at the start of every new chat.**

| App | Status |
|-----|--------|
| `accounts/` | ✅ Done |
| `questions/` | 🔧 In progress |
| `exams/` | ⬜ Not started |
| `dashboard/` | ⬜ Not started |
| `org/` | ⬜ Not started |
| `students/` | ⬜ Not started |
| `core/` | ⬜ Not started |

Statuses: ⬜ Not started · 🔧 In progress · ✅ Done

---

## Tech Stack
- Python 3.12+, Django 5.x, PostgreSQL
- uv (package manager), Docker + Docker Compose
- Bootstrap 5, django-crispy-forms + crispy-bootstrap5
- Pillow, whitenoise, gunicorn, nginx
- Environment variables via `os.environ` (no django-environ)

---

## Three User Roles
**Admin** (internal team) — manages all content via Django admin. Adds global questions, tags, manages organizations and all users.

**Org Admin** (course owner / department head) — logs in to org panel. Manages their own teachers. Can view/edit all questions within their organization. Sees exam statistics and student statistics across their organization.

**Teacher** (client users) — logs in to a custom dashboard. Generates exams. Can add questions scoped to their own organization (only edit their own questions). Adds students and tracks their exam results.

---

## App Structure

```
accounts/    # Custom user model, Organization model, login/logout, role-based redirect
questions/   # Question, Choice, Tag, TagCategory models + admin (global) + teacher-facing views (org-scoped)
exams/       # Exam generation algorithm (services.py), Exam model
dashboard/   # Teacher-facing panel, exam history — no models, reads from exams/ and students/
org/         # Org Admin panel — no models, reads from accounts/, questions/, exams/, students/
students/    # Student model, exam result tracking — teacher-facing
core/        # Shared mixins, context processors, template tags — no models, no migrations
```

---

## URL Structure

| URL | View | App | Who |
|-----|------|-----|-----|
| `/login/` | `login_view` | accounts | All |
| `/logout/` | `logout_view` | accounts | All |
| `/dashboard/` | `DashboardHomeView` | dashboard | Teacher |
| `/dashboard/profile/` | `ProfileView` | dashboard | Teacher |
| `/questions/` | `QuestionListView` | questions | Teacher |
| `/questions/add/` | `QuestionCreateView` | questions | Teacher |
| `/questions/<id>/edit/` | `QuestionUpdateView` | questions | Teacher (own only) |
| `/exams/create/` | `ExamCreateView` | exams | Teacher |
| `/exams/<id>/preview/` | `ExamPreviewView` | exams | Teacher |
| `/exams/history/` | `ExamHistoryView` | exams | Teacher |
| `/students/` | `StudentListView` | students | Teacher |
| `/students/add/` | `StudentCreateView` | students | Teacher |
| `/students/<id>/` | `StudentDetailView` | students | Teacher |
| `/org/` | `OrgDashboardView` | org | Org Admin |
| `/org/teachers/` | `TeacherListView` | org | Org Admin |
| `/org/teachers/add/` | `TeacherCreateView` | org | Org Admin |
| `/org/teachers/<id>/` | `TeacherDetailView` | org | Org Admin |
| `/org/questions/` | `OrgQuestionListView` | org | Org Admin |
| `/org/questions/<id>/edit/` | `OrgQuestionUpdateView` | org | Org Admin |
| `/org/exams/` | `OrgExamListView` | org | Org Admin |
| `/org/students/` | `OrgStudentListView` | org | Org Admin |
| `/admin/` | Django admin | — | Admin (you) |

---

## Core Models

### accounts
- **Organization** → `name`, `slug`, `created_at`
- **User** (AbstractUser) → `role` (admin/org_admin/teacher), `organization` FK
  - `first_name` and `last_name` → inherited from AbstractUser, required (`blank=False`)
  - Used to display question ownership (`created_by.get_full_name()`)

### questions
- **TagCategory** → `name` (e.g. Grammar, Skill, Format)
- **Tag** → `name`, `category` FK
- **Question** → `level` (A1–C2), `text`, `image`, `tags` M2M, `is_active`,
  `organization` FK (null=True → global question), `created_by` FK (null=True → added by admin)
- **Choice** → `question` FK, `text`, `is_correct`

#### Question pool logic
| `organization` | `created_by` | Meaning |
|---|---|---|
| `None` | `None` | Global question added by admin |
| `None` | admin user | Global question added by admin |
| School A | Teacher X | School A specific, added by Teacher X |

### exams
- **Exam** → `teacher` FK, `organization` FK, `parameters` JSONField, `questions` M2M, `created_at`

`parameters` JSON example:
```json
{
  "total": 20,
  "levels": {
    "B1": {"min": 40, "max": 60},
    "B2": {"min": 20, "max": 40}
  },
  "tags": [3, 7]
}
```

### students
- **Student** → `first_name`, `last_name`, `organization` FK, `teacher` FK (User), `created_at`
  - Not a User — cannot log in
  - Represents a real student tracked by a teacher
- **ExamResult** → `student` FK, `exam` FK, `score`, `date`, `notes`

---

## Question Types
All questions use the same model. Type is determined by tags:
- **Multiple Choice** → tag: "Multiple Choice", has 4 choices
- **True/False** → tag: "True/False", has 2 choices
- **Fill in the Blank** → tag: "Fill in the Blank", no choices — ⚠️ correct answer storage TBD (pending content team decision)

---

## Business Rules

### Question Rules
- `is_active=False` questions are never included in exam generation
- A question cannot appear twice in the same exam
- Teachers can only edit questions they created (`created_by=request.user`)
- Teachers can view global questions (read-only) + their own org questions
- Org Admins can view and edit all questions within their organization
- `organization` and `created_by` are set automatically by the view — teachers do not select them in the form

### Exam Rules
- Teachers can only see exams belonging to their own organization
- Org Admins can see all exams within their organization
- If not enough questions exist for given constraints, return a user-facing error (do not silently skip)

### Student Rules
- Students are not users — they cannot log in
- Teachers can only see/edit their own students (`teacher=request.user`)
- Org Admins can see all students within their organization
- ExamResult links a student to an exam with a score

### Org Admin Rules
- Org Admins can add teachers to their own organization only
- Org Admins cannot add other Org Admins (only Admin can do that)
- Org Admins cannot access other organizations' data

---

## Exam Generation Logic
Teacher inputs: total question count + per-level min/max percentage ranges + optional tag filters.

Algorithm flow (`exams/services.py`):
1. `_calculate_counts()` — convert ratio inputs into exact per-level question counts
2. `_filter_questions()` — apply level + tag filters; global questions (org=None) + teacher's org questions combined:
   ```python
   Question.objects.filter(is_active=True).filter(
       Q(organization=None) | Q(organization=teacher.organization)
   )
   ```
3. `_validate_counts()` — check if enough active questions exist; raise error if not
4. `_sample_questions()` — draw randomly using `random.sample`
5. `generate()` — orchestrates all above, saves and returns the Exam instance

---

## Auth Flow
- Login → check role:
  - `admin` → `/admin/`
  - `org_admin` → `/org/`
  - `teacher` → `/dashboard/`
- Django session auth (no JWT, no API keys)

---

## App Details

### `accounts/`
**Purpose:** User authentication, organization management, role-based routing.

| File | Content |
|------|---------|
| `models.py` | `Organization`, `User` (AbstractUser with role + organization FK) |
| `views.py` | `login_view`, `logout_view`, `role_redirect_view` |
| `forms.py` | `LoginForm` |
| `mixins.py` | `TeacherRequiredMixin`, `OrgAdminRequiredMixin`, `AdminRequiredMixin` |
| `admin.py` | `UserAdmin` (organization + role visible), `OrganizationAdmin` |

---

### `questions/`
**Purpose:** Question bank content management. Global questions managed via Django admin. Org-specific questions added via teacher-facing views.

| File | Content |
|------|---------|
| `models.py` | `TagCategory`, `Tag`, `Question` (organization + created_by FK), `Choice` |
| `admin.py` | `ChoiceInline`, `QuestionAdmin` (level/tag/is_active/organization filters), `TagAdmin`, `TagCategoryAdmin` |
| `views.py` | `QuestionListView`, `QuestionCreateView`, `QuestionUpdateView` (teacher-only, org-scoped, own questions only) |
| `forms.py` | `QuestionForm`, `ChoiceForm`, `ChoiceFormSet` (organization and created_by excluded from QuestionForm — set automatically in view) |

### `exams/`
**Purpose:** Exam generation algorithm and exam history.

| File | Content |
|------|---------|
| `models.py` | `Exam` |
| `services.py` | `ExamGeneratorService` — full algorithm, independent from views |
| `views.py` | `ExamCreateView`, `ExamPreviewView`, `ExamHistoryView` |
| `forms.py` | `ExamGenerationForm` (total count, per-level min/max, tag selection) |

---

### `students/`
**Purpose:** Student tracking and exam result management. Students are not users.

| File | Content |
|------|---------|
| `models.py` | `Student`, `ExamResult` |
| `views.py` | `StudentListView`, `StudentCreateView`, `StudentDetailView` |
| `forms.py` | `StudentForm`, `ExamResultForm` |

---

### `dashboard/`
**Purpose:** Teacher-facing panel. No models — only reads from `exams/` and `students/`.

| File | Content |
|------|---------|
| `views.py` | `DashboardHomeView` (recent exams + stats), `ProfileView` (read-only profile) |

---

### `org/`
**Purpose:** Org Admin panel. No models — reads from `accounts/`, `questions/`, `exams/`, `students/`.

| File | Content |
|------|---------|
| `views.py` | `OrgDashboardView`, `TeacherListView`, `TeacherCreateView`, `TeacherDetailView`, `OrgQuestionListView`, `OrgQuestionUpdateView`, `OrgExamListView`, `OrgStudentListView` |
| `forms.py` | `TeacherCreateForm` (creates a User with role=teacher, same organization as org_admin) |

---

### `core/`
**Purpose:** Shared helpers used across multiple apps. No models, no migrations.

| File | Content |
|------|---------|
| `apps.py` | to be able to add INSTALLED_APPS in config/settings|
| `mixins.py` | `OrgFilterMixin` — filters querysets by `request.user.organization` |
| `context_processors.py` | `user_role_context` — injects `role` into every template context |
| `templatetags/__init__.py` | empty file, to define as python package |
| `templatetags/core_tags.py` | `active_nav` — marks active nav link with Bootstrap `active` class |

---

## General Request Flow

```
Browser
  → accounts/        (login, role check)
  ↓
  ├── /admin/        (Admin — you, manages everything)
  │
  ├── /org/          (Org Admin — manages teachers, views questions/exams/students)
  │
  └── /dashboard/    (Teacher — adds questions, creates exams, tracks students)
        → questions/     (teacher adds/edits own questions)
        → exams/create   (form: count + level ratios + tag filters)
        → services.py    (ExamGeneratorService: global + org questions combined)
        → exams/preview  (generated exam displayed, print button)
        → students/      (teacher adds students, records exam results)
```

---

## Settings Structure
```
settings/
  base.py        # shared config
  local.py       # DEBUG=True, local DB
  production.py  # DEBUG=False, real SECRET_KEY, allowed hosts
```

---

## What Is NOT in This Project
- No REST API or API keys
- No student login (students are tracked records, not users)
- No CSV/Excel import (planned for future)
- No JWT or token auth
- No frontend framework (Django templates only)

---

## How to Use This File
1. Paste this file at the start of every new chat
2. Update the **Current Status** table to reflect what's done
3. State which app/area you're working on

## Example run command
- `docker compose exec web uv run python manage.py check`

## Examples
- "I'm working on the accounts app, how should I structure login_view?"
- "Let's write the _calculate_counts method of ExamGeneratorService together."
- "Teacher should only see their own org's exams, how do I apply OrgFilterMixin?"
- "How do I set up ChoiceInline in Question admin?"
- "How are organization and created_by set automatically when a teacher adds a question?"
- "How does OrgAdmin create a teacher account in their own organization?"



## Notes 
## Daha sonra düzenlenecek ve belki geri dönülecek 
### Permissions (Sonraya Bırakıldı)
- `role=teacher` kaydedilince teacher izinleri otomatik atanacak
- `role=org_admin` kaydedilince org_admin izinleri otomatik atanacak
- Elle seçim yapılmayacak — signal veya `save()` override ile çözülecek
- Mixin'ler tamamlandıktan sonra hangi izinlerin gerekli olduğu netleşecek

öğretmen sınav 

#### Değişiklikler 
- Öğretmenler kendi sorularını eklemeyecekler 
- Soruları sadece contibutor'lar ekleyecek (mali buğra vs )
- Ses kısmı eklenecek (listening)
- Organizations kısmı altında teachers bağlı olmasına gerek yok ama her öğretmen için ekleyebiliriz bir noktada kullandıkları soruları
index olarak tutup aynı hocaya aynı soru denk gelmemesi için 
- yani contibutor eklenecek soruları ekleyen kişiler için olacak, teacher soru ekleyemeyecek students adı altında sınav takip sistemleri olmayacak teacherlar sadece soruları çekip pdf olarak indirebilecek ek olarak ses kısmı için indirme kısmı eklenecek veya link çıkacak 
