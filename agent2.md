# Project Context: English Question Bank System

## What This Is
A Django web application for English language schools. Teachers log in and generate automatic exams from a question bank, then download them as PDF. No public API, no mobile app — web only.

---

## Current Status
> **Update this section at the start of every new chat.**

| App | Status |
|-----|--------|
| `accounts/` | ✅ Done |
| `questions/` | ✅ Done |
| `exams/` | 🔧 In progress  |
| `dashboard/` | ⬜ Not started |
| `org/` | ⬜ Not started |
| `core/` | ✅ Done |

Statuses: ⬜ Not started · 🔧 In progress · ✅ Done

> **Note:** `students/` app removed from scope. Teachers no longer add questions — contributors do.

---

## Tech Stack
- Python 3.12+, Django 5.x, PostgreSQL
- uv (package manager), Docker + Docker Compose
- Bootstrap 5, django-crispy-forms + crispy-bootstrap5
- Pillow, whitenoise, gunicorn, nginx
- Environment variables via `os.environ` (no django-environ)

---

## Four User Roles
**Admin** (internal team) — manages all content via Django admin. Adds global questions, tags, manages organizations and all users.

**Contributor** (content team — e.g. Mali, Buğra) — logs in to a contributor panel. Adds and edits questions (global or org-scoped). Cannot manage users or organizations.

**Org Admin** (course owner / department head) — logs in to org panel. Manages their own teachers. Can view all questions within their organization. Sees exam statistics across their organization.

**Teacher** (client users) — logs in to a custom dashboard. Generates exams and downloads them as PDF. Cannot add or edit questions. Adds students via the student panel are removed; teachers only track which exams they generated.

---

## App Structure

```
accounts/    # Custom user model, Organization model, login/logout, role-based redirect
questions/   # Question, Choice, Tag, TagCategory models + admin + contributor-facing views
exams/       # Exam generation algorithm (services.py), Exam model, PDF export
dashboard/   # Teacher-facing panel, exam history — no models, reads from exams/
org/         # Org Admin panel — no models, reads from accounts/, questions/, exams/
core/        # Shared mixins, context processors, template tags — no models, no migrations
```

> **Removed:** `students/` app (Student model, ExamResult, student tracking) is out of scope.

---

## URL Structure

| URL | View | App | Who |
|-----|------|-----|-----|
| `/login/` | `login_view` | accounts | All |
| `/logout/` | `logout_view` | accounts | All |
| `/dashboard/` | `DashboardHomeView` | dashboard | Teacher |
| `/dashboard/profile/` | `ProfileView` | dashboard | Teacher |
| `/exams/create/` | `ExamCreateView` | exams | Teacher |
| `/exams/<id>/preview/` | `ExamPreviewView` | exams | Teacher |
| `/exams/<id>/download/` | `ExamDownloadView` | exams | Teacher (PDF) |
| `/exams/history/` | `ExamHistoryView` | exams | Teacher |
| `/questions/` | `QuestionListView` | questions | Contributor |
| `/questions/add/` | `QuestionCreateView` | questions | Contributor |
| `/questions/<id>/edit/` | `QuestionUpdateView` | questions | Contributor (own only) |
| `/org/` | `OrgDashboardView` | org | Org Admin |
| `/org/teachers/` | `TeacherListView` | org | Org Admin |
| `/org/teachers/add/` | `TeacherCreateView` | org | Org Admin |
| `/org/teachers/<id>/` | `TeacherDetailView` | org | Org Admin |
| `/org/questions/` | `OrgQuestionListView` | org | Org Admin |
| `/org/exams/` | `OrgExamListView` | org | Org Admin |
| `/admin/` | Django admin | — | Admin (you) |

> **Removed:** `/students/` URLs — student tracking is out of scope.

---

## Core Models

### accounts
- **Organization** → `name`, `slug`, `created_at`
- **User** (AbstractUser) → `role` (admin/org_admin/contributor/teacher), `organization` FK
  - `first_name` and `last_name` → inherited from AbstractUser, required (`blank=False`)
  - Used to display question ownership (`created_by.get_full_name()`)

### questions
- **TagCategory** → `name` (e.g. Grammar, Skill, Format)
- **Tag** → `name`, `category` FK
- **Question** → `level` (A1–C2), `text`, `image`, `audio`, `is_active`,
  `organization` FK (null=True → global question), `created_by` FK (null=True → added by admin)
- **Choice** → `question` FK, `text`, `is_correct`

#### Audio field
Questions may include an audio file for listening exercises. `audio` is a `FileField` (upload_to=`questions/audio/`). If present, the exam preview and PDF export show a download link or streaming player. Teachers cannot add/edit audio — contributors and admin manage it.

#### Question pool logic
| `organization` | `created_by` | Meaning |
|---|---|---|
| `None` | `None` | Global question added by admin |
| `None` | admin/contributor user | Global question added by admin or contributor |
| School A | Contributor X | School A specific, added by Contributor X |

### exams
- **Exam** → `teacher` FK, `organization` FK, `parameters` JSONField, `questions` M2M, `created_at`
- **TeacherQuestionIndex** → `teacher` FK, `question` FK, `used_at` — tracks which questions a teacher has already received, so the same question is never given to the same teacher twice.

`parameters` JSON example:
```json
{
  "total": 20,
  "levels": {
    "B1": 8,
    "B2": 6,
    "C1": 6
  },
  "tags": [3, 7]
}
```

---

## Question Types
All questions use the same model. Type is determined by tags:
- **Multiple Choice** → tag: "Multiple Choice", has 4 choices
- **True/False** → tag: "True/False", has 2 choices
- **Fill in the Blank** → tag: "Fill in the Blank", no choices — ⚠️ correct answer storage TBD (pending content team decision)
- **Listening** → tag: "Listening", has an `audio` file attached

---

## Business Rules

### Question Rules
- `is_active=False` questions are never included in exam generation
- A question cannot appear twice in the same exam
- **Teachers cannot add or edit questions** — only contributors and admin can
- Contributors can only edit questions they created (`created_by=request.user`)
- Contributors can view global questions (read-only) + questions in their own org (if org-scoped)
- Org Admins can view all questions within their organization (read-only in the org panel)
- `organization` and `created_by` are set automatically by the view — contributors do not select them in the form

### Exam Rules
- Teachers can only see exams they generated (filtered by `teacher=request.user`)
- Org Admins can see all exams within their organization
- If not enough questions exist for given constraints, return a user-facing error (do not silently skip)
- **Teacher Question Index:** when generating an exam, questions already in a teacher's index are excluded first. After generation, all selected questions are added to that teacher's index. This prevents the same question from appearing in a later exam for the same teacher.

### Org Admin Rules
- Org Admins can add teachers to their own organization only
- Org Admins cannot add other Org Admins (only Admin can do that)
- Org Admins cannot access other organizations' data

---

## Exam Generation Logic
Teacher inputs: total question count + exact per-level question counts (must sum to total) + optional tag filters.
Algorithm flow (`exams/services.py`):
1. `_calculate_counts()` - validate that per-level counts sum to the total (counts are already exact, entered directly by the teacher)
2. `_filter_questions()` — apply level + tag filters; global questions (org=None) + teacher's org questions combined. **Exclude questions already in the teacher's index:**
   ```python
   used_ids = TeacherQuestionIndex.objects.filter(teacher=teacher).values_list('question_id', flat=True)
   Question.objects.filter(is_active=True).filter(
       Q(organization=None) | Q(organization=teacher.organization)
   ).exclude(id__in=used_ids)
   ```
3. `_validate_counts()` — check if enough active questions exist; raise error if not
4. `_sample_questions()` — draw randomly using `random.sample`
5. `_update_index()` — add selected questions to `TeacherQuestionIndex` for this teacher
6. `generate()` — orchestrates all above, saves and returns the Exam instance

---

## PDF Export
After generating an exam, teachers can download it as a PDF:
- Questions and choices are rendered into a clean printable layout
- If a question has an `audio` file, the PDF shows a QR code or short URL linking to the audio file (teachers cannot embed audio in PDF)
- Implemented in `exams/views.py` as `ExamDownloadView` using a PDF library (e.g. `reportlab` or `weasyprint`)

---

## Auth Flow
- Login → check role:
  - `admin` → `/admin/`
  - `org_admin` → `/org/`
  - `contributor` → `/questions/`
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
| `mixins.py` | `TeacherRequiredMixin`, `ContributorRequiredMixin`, `OrgAdminRequiredMixin`, `AdminRequiredMixin` |
| `admin.py` | `UserAdmin` (organization + role visible), `OrganizationAdmin` |

> **Changed:** `role` now has four choices: `admin`, `org_admin`, `contributor`, `teacher`.
> **Added:** `ContributorRequiredMixin` in `mixins.py`.

---

### `questions/`
**Purpose:** Question bank content management. Global questions managed via Django admin or contributor panel. Org-specific questions added by contributors.

| File | Content |
|------|---------|
| `models.py` | `TagCategory`, `Tag`, `Question` (organization + created_by FK, audio FileField), `Choice` |
| `admin.py` | `ChoiceInline`, `QuestionAdmin` (level/tag/is_active/organization filters), `TagAdmin`, `TagCategoryAdmin` |
| `views.py` | `QuestionListView`, `QuestionCreateView`, `QuestionUpdateView` (contributor-only, own questions only) |
| `forms.py` | `QuestionForm`, `ChoiceForm`, `ChoiceFormSet` (organization and created_by excluded — set automatically in view) |

> **Changed:** Views are now `ContributorRequiredMixin` — teachers cannot access these URLs.

---

### `exams/`
**Purpose:** Exam generation algorithm, exam history, and PDF download.

| File | Content |
|------|---------|
| `models.py` | `Exam`, `TeacherQuestionIndex` |
| `services.py` | `ExamGeneratorService` — full algorithm including index update |
| `views.py` | `ExamCreateView`, `ExamPreviewView`, `ExamDownloadView` (PDF), `ExamHistoryView` |
| `forms.py` | `ExamGenerationForm` (total question count, Exact question count per level (6 inputs, one per CEFR level, JS-validated to sum to total), Multi-select tags) |

> **Added:** `TeacherQuestionIndex` model and `ExamDownloadView`.

---

### `dashboard/`
**Purpose:** Teacher-facing panel. No models — only reads from `exams/`.

| File | Content |
|------|---------|
| `views.py` | `DashboardHomeView` (recent exams + stats), `ProfileView` (read-only profile) |

> **Changed:** Student stats removed. Dashboard now shows recent exams and total exam count only.

---

### `org/`
**Purpose:** Org Admin panel. No models — reads from `accounts/`, `questions/`, `exams/`.

| File | Content |
|------|---------|
| `views.py` | `OrgDashboardView`, `TeacherListView`, `TeacherCreateView`, `TeacherDetailView`, `OrgQuestionListView`, `OrgExamListView` |
| `forms.py` | `TeacherCreateForm` (creates a User with role=teacher, same organization as org_admin) |

> **Removed:** `OrgStudentListView`, `OrgQuestionUpdateView` (org admin views questions read-only).

---

### `core/`
**Purpose:** Shared helpers used across multiple apps. No models, no migrations.

| File | Content |
|------|---------|
| `apps.py` | to be able to add INSTALLED_APPS in config/settings |
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
  ├── /admin/        (Admin — manages everything)
  │
  ├── /questions/    (Contributor — adds/edits questions, manages audio)
  │
  ├── /org/          (Org Admin — manages teachers, views questions/exams)
  │
  └── /dashboard/    (Teacher — creates exams, downloads PDF)
        → exams/create    (form: count + level ratios + tag filters)
        → services.py     (ExamGeneratorService: global + org questions, excludes teacher's index)
        → exams/preview   (generated exam displayed)
        → exams/download  (PDF export, audio linked via QR/URL)
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
- No student login or student tracking (students app removed)
- No CSV/Excel import (planned for future)
- No JWT or token auth
- No frontend framework (Django templates only)
- Teachers cannot add or edit questions

---

## How to Use This File
1. Paste this file at the start of every new chat
2. Update the **Current Status** table to reflect what's done
3. State which app/area you're working on

## Example run command
- `docker compose exec web uv run python manage.py check`

## Examples
- "I'm working on the accounts app, how should I add the contributor role?"
- "Let's write the _calculate_counts method of ExamGeneratorService together."
- "Teacher should only see exams they generated, how do I filter that?"
- "How does TeacherQuestionIndex prevent duplicate questions across exams?"
- "How does OrgAdmin create a teacher account in their own organization?"
- "How do I generate a PDF with audio links in ExamDownloadView?"

---

## Notes
### Permissions (Sonraya Bırakıldı)
- `role=teacher` kaydedilince teacher izinleri otomatik atanacak
- `role=org_admin` kaydedilince org_admin izinleri otomatik atanacak
- `role=contributor` kaydedilince contributor izinleri otomatik atanacak
- Elle seçim yapılmayacak — signal veya `save()` override ile çözülecek
- Mixin'ler tamamlandıktan sonra hangi izinlerin gerekli olduğu netleşecek
