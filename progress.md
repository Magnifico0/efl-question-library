# Build Progress — English Question Bank System

> Check off each step as you complete it: `[ ]` → `[x]`
> Paste this file together with agent.md at the start of every new chat.

---

## Why This Order?

```
Project setup
  → accounts/   (everything depends on User, must come first)
    → core/     (mixins depend on accounts)
      → questions/  (question bank, requires User + Org)
        → students/   (requires User + Org)
          → exams/    (requires questions + accounts + students)
            → dashboard/  (reads from exams + students, comes last)
              → org/      (reads from everything, comes last)
                → Polish  (templates, static, deploy)
```

---

## Stage 0 — Project Setup

- [x] Create new project with `uv`, prepare `pyproject.toml`
- [x] `django-admin startproject config .` — project name `config`
- [x] Create `settings/` folder: `base.py`, `local.py`, `production.py`
- [x] Move base settings to `base.py` (INSTALLED_APPS, TEMPLATES, STATIC, MEDIA)
- [x] `local.py`: DEBUG=True, local PostgreSQL connection
- [x] `production.py`: DEBUG=False, SECRET_KEY from env, ALLOWED_HOSTS
- [x] Write `docker-compose.yml`: `web` + `db` services
- [x] Write `Dockerfile`
- [x] Create `.env.example`
- [x] `python manage.py check` passes without errors

**Check:** `docker compose up` brings the project up, Django welcome page visible.

---

## Stage 1 — `accounts/` App

> All other apps depend on User and Organization. Nothing else can be written without this.

### 1.1 Models
- [x] Create `accounts` app, add to `INSTALLED_APPS`
- [x] Write `Organization` model: `name`, `slug`, `created_at`
- [x] Write `User` model (AbstractUser):
  - `role` → `CharField(choices=[admin, org_admin, teacher])`
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `first_name` and `last_name` → override with `blank=False` (required)
- [x] Add `AUTH_USER_MODEL = 'accounts.User'` to `settings/base.py`
- [x] Create and apply migration — **must be done before any other migrations**

### 1.2 Admin
- [x] Write `OrganizationAdmin`
- [x] Write `UserAdmin`: `role`, `organization`, `first_name`, `last_name` visible

### 1.3 Auth Views
- [x] Write `LoginForm` (`forms.py`)
- [x] Write `login_view`: POST → role check → admin to `/admin/`, org_admin to `/org/`, teacher to `/dashboard/`
- [x] Write `logout_view`
- [x] Write `role_redirect_view` (redirect already logged-in users to correct page)
- [x] Wire up URLs: `/login/`, `/logout/`

### 1.4 Mixins
- [x] Write `TeacherRequiredMixin`
- [x] Write `OrgAdminRequiredMixin`
- [x] Write `AdminRequiredMixin`

### 1.5 Template
- [x] Write `templates/accounts/login.html` (Bootstrap 5)

**Check:** Login as admin, org_admin, and teacher — each redirects to the correct page. Visiting `/dashboard/` without login redirects to `/login/`.

---

## Stage 2 — `core/` App

> Shared tools used by other apps. Write early so they're ready for later stages.

- [x] Create `core` app (no migrations folder — specify in `AppConfig`)
- [x] Write `OrgFilterMixin`: filter querysets by `request.user.organization`
- [x] Write `user_role_context` context processor: inject `role` into every template
- [x] Add context processor to `settings/base.py`
- [x] Create `core/templatetags/` folder
- [x] Write `active_nav` template tag: add Bootstrap `active` class to active nav link

**Check:** Writing `{{ role }}` in any template returns the correct value.

---

## Stage 3 — `questions/` App

### 3.1 Models
- [x] Create `questions` app
- [x] Write `TagCategory` model: `name`
- [x] Write `Tag` model: `name`, `category` FK
- [x] Write `Question` model:
  - `level` → `CharField(choices=[A1, A2, B1, B2, C1, C2])`
  - `text`, `image` (Pillow), `is_active`
  - `tags` → M2M (Tag)
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `created_by` → `ForeignKey(User, null=True, blank=True)`
- [x] Write `Choice` model: `question` FK, `text`, `is_correct`
- [x] Create and apply migration

### 3.2 Admin (Global Questions)
- [x] Write `ChoiceInline` (inline choice entry inside Question admin)
- [x] Write `QuestionAdmin`: level / tag / is_active / organization filters
- [x] Write `TagAdmin` and `TagCategoryAdmin`
- [x] Add a few sample questions via admin (for testing)

### 3.3 Teacher-Facing Views (Org-Scoped Questions)
- [x] Write `QuestionForm`: `organization` and `created_by` fields **not in form**
- [x] Write `ChoiceForm` and `ChoiceFormSet`: inline choice entry for teacher-facing question form
- [ ] Write `QuestionListView`: only questions where `created_by=request.user`
- [ ] Write `QuestionCreateView`:
  - Set `organization` and `created_by` automatically in `form_valid()`
  - Use `TeacherRequiredMixin`
  - Handle `ChoiceFormSet` inline (min 2 choices required, no choices → is_active=False)
- [ ] Write `QuestionUpdateView`: teacher can only edit their own questions
- [ ] Wire up URLs: `/questions/`, `/questions/add/`, `/questions/<id>/edit/`
- [ ] Write templates: list and form pages

**Check:** Admin can add global questions. Teacher can add and list their own questions. Teacher cannot edit another teacher's question.

---

## Stage 4 — `students/` App

> Students are not users — they are records tracked by teachers.

### 4.1 Models
- [ ] Create `students` app
- [ ] Write `Student` model:
  - `first_name`, `last_name`
  - `organization` → FK (Organization)
  - `teacher` → FK (User)
  - `created_at`
- [ ] Write `ExamResult` model:
  - `student` → FK (Student)
  - `exam` → FK (Exam)
  - `score`
  - `date`
  - `notes` (optional)
- [ ] Create and apply migration

### 4.2 Forms
- [ ] Write `StudentForm`: `organization` and `teacher` set automatically in view
- [ ] Write `ExamResultForm`

### 4.3 Views
- [ ] Write `StudentListView`: only `teacher=request.user` students
- [ ] Write `StudentCreateView`: set `organization` and `teacher` automatically
- [ ] Write `StudentDetailView`: student info + exam results list
- [ ] Wire up URLs: `/students/`, `/students/add/`, `/students/<id>/`
- [ ] Write templates

**Check:** Teacher can add students and record exam results. Teacher cannot see another teacher's students.

---

## Stage 5 — `exams/` App

### 5.1 Model
- [ ] Create `exams` app
- [ ] Write `Exam` model:
  - `teacher` FK (User)
  - `organization` FK (Organization)
  - `parameters` JSONField
  - `questions` M2M (Question)
  - `created_at`
- [ ] Create and apply migration

### 5.2 Service Layer (`services.py`)
> Write independently from views. Must be testable.

- [ ] Create `ExamGeneratorService` class, accept `teacher` and `params` in constructor
- [ ] `_calculate_counts()` → convert percentage ranges to exact counts
- [ ] `_filter_questions()` → level + tag filter + `Q(org=None) | Q(org=teacher.org)`
- [ ] `_validate_counts()` → raise meaningful error if not enough questions
- [ ] `_sample_questions()` → draw randomly with `random.sample`, no duplicates
- [ ] `generate()` → orchestrate all above, create and return `Exam` instance

### 5.3 Form
- [ ] Write `ExamGenerationForm`:
  - Total question count
  - Min/max percentage fields per level
  - Multi-select tags

### 5.4 Views
- [ ] Write `ExamCreateView`: call `ExamGeneratorService.generate()` if form is valid
- [ ] Write `ExamPreviewView`: display exam, print button
- [ ] Write `ExamHistoryView`: only own org exams via `OrgFilterMixin`
- [ ] Wire up URLs

### 5.5 Templates
- [ ] `exams/create.html` — form page
- [ ] `exams/preview.html` — exam preview + print button
- [ ] `exams/history.html` — past exams list

**Check:** Create an exam, all questions visible in preview. Error message shown when not enough questions. Another org's exam is inaccessible via URL.

---

## Stage 6 — `dashboard/` App

- [ ] Create `dashboard` app (no models.py, no migrations)
- [ ] Write `DashboardHomeView`: last 5 exams + total exam count stat + student count
- [ ] Write `ProfileView`: read-only user info
- [ ] Wire up URLs: `/dashboard/`, `/dashboard/profile/`
- [ ] Write `templates/dashboard/home.html`
- [ ] Write `templates/dashboard/profile.html`
- [ ] Add question bank and create exam links to `base.html` nav

**Check:** Recent exams visible on dashboard. Nav links work correctly.

---

## Stage 7 — `org/` App

> Org Admin panel. No models — reads from other apps.

- [ ] Create `org` app (no models.py, no migrations)
- [ ] Write `OrgDashboardView`: teacher count, question count, exam count, student count for the org
- [ ] Write `TeacherListView`: all teachers in org
- [ ] Write `TeacherCreateView`: create User with `role=teacher`, same org as org_admin
- [ ] Write `TeacherDetailView`: teacher info + their questions + their students
- [ ] Write `OrgQuestionListView`: all questions in org
- [ ] Write `OrgQuestionUpdateView`: org_admin can edit any question in their org
- [ ] Write `OrgExamListView`: all exams in org
- [ ] Write `OrgStudentListView`: all students in org
- [ ] Wire up URLs: `/org/`, `/org/teachers/`, `/org/questions/`, `/org/exams/`, `/org/students/`
- [ ] Write templates

**Check:** Org Admin can add a teacher. Org Admin can edit any question in their org. Org Admin cannot access another org's data.

---

## Stage 8 — Polish & Deploy Prep

### General Templates
- [ ] `templates/base.html` — Bootstrap 5 navbar, footer, block structure
- [ ] `templates/404.html`, `templates/500.html`
- [ ] Add Django messages framework flash messages to base.html

### Static Files
- [ ] Add WhiteNoise settings to `base.py`
- [ ] `python manage.py collectstatic` passes without errors

### Security & Production
- [ ] Set CSRF, SESSION, SECURE settings in `production.py`
- [ ] Write `nginx.conf`
- [ ] Write `docker-compose.prod.yml`
- [ ] Document `.env` variables

### Final Checks
- [ ] All views have login_required or a mixin?
- [ ] Teacher cannot access another org's exams/questions via URL?
- [ ] Org Admin cannot access another org's data via URL?
- [ ] `is_active=False` questions never included in exam generation?
- [ ] `python manage.py check --deploy` passes without warnings?

---

## Summary Table

| Stage | Content | Depends On |
|---|---|---|
| 0 | Project setup | — |
| 1 | `accounts/` | 0 |
| 2 | `core/` | 1 |
| 3 | `questions/` | 1, 2 |
| 4 | `students/` | 1, 2 |
| 5 | `exams/` | 1, 2, 3, 4 |
| 6 | `dashboard/` | 1, 5 |
| 7 | `org/` | 1, 3, 5, 4 |
| 8 | Polish & Deploy | 1–7 |

# NOTES 
## DUZENLENECEK
- [ ] **NOT:** `role` teacher veya org_admin olarak kaydedilince `user permissions` otomatik atansın — signal veya `save()` override ile yapılacak, mixin'ler tamamlandıktan sonra
