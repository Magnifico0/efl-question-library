# Project Context: English Question Bank System

## What This Is
A Django web application for English language schools. Teachers log in and generate automatic exams from a question bank. No public API, no mobile app — web only.

---

## Current Status
> **Update this section at the start of every new chat.**

| App | Status |
|-----|--------|
| `accounts/` | ⬜ Not started |
| `questions/` | ⬜ Not started |
| `exams/` | ⬜ Not started |
| `dashboard/` | ⬜ Not started |
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

## Two User Roles
**Admin** (internal team) — manages all content via Django admin. Adds global questions, tags, manages organizations.
**Teacher** (client users) — logs in to a custom dashboard. Generates exams. Can add questions scoped to their own organization. Sees only their organization's data.

---

## App Structure

```
accounts/    # Custom user model, Organization model, login/logout, role-based redirect
questions/   # Question, Choice, Tag, TagCategory models + admin (global) + teacher-facing views (org-scoped)
exams/       # Exam generation algorithm (services.py), Exam model
dashboard/   # Teacher-facing panel, exam history — no models, reads from exams/
core/        # Shared mixins, context processors, template tags — no models, no migrations
```

---

## URL Structure

| URL | View | App |
|-----|------|-----|
| `/login/` | `login_view` | accounts |
| `/logout/` | `logout_view` | accounts |
| `/dashboard/` | `DashboardHomeView` | dashboard |
| `/dashboard/profile/` | `ProfileView` | dashboard |
| `/questions/` | `QuestionListView` | questions |
| `/questions/add/` | `QuestionCreateView` | questions |
| `/questions/<id>/edit/` | `QuestionUpdateView` | questions |
| `/exams/create/` | `ExamCreateView` | exams |
| `/exams/<id>/preview/` | `ExamPreviewView` | exams |
| `/exams/history/` | `ExamHistoryView` | exams |
| `/admin/` | Django admin | — |

---

## Core Models

### accounts
- **Organization** → `name`, `slug`, `created_at`
- **User** (AbstractUser) → `role` (admin/teacher), `organization` FK
  - `first_name` ve `last_name` → AbstractUser'dan gelir, kayıt sırasında **zorunlu** tutulur
  - Bu alanlar soru sahipliğini göstermek için kullanılır (`created_by.get_full_name()`)

### questions
- **TagCategory** → `name` (e.g. Grammar, Skill, Format)
- **Tag** → `name`, `category` FK
- **Question** → `level` (A1–C2), `text`, `image`, `tags` M2M, `is_active`,
  `organization` FK (null=True → global soru), `created_by` FK (null=True → admin ekledi)
- **Choice** → `question` FK, `text`, `is_correct`

#### Question havuzu mantığı
| `organization` | `created_by` | Anlamı |
|---|---|---|
| `None` | `None` | Admin'in eklediği global soru |
| `None` | admin user | Admin'in eklediği global soru |
| Okul A | Teacher X | Okul A'ya özel, Teacher X'in eklediği soru |

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

---

## Question Types
All questions use the same model. Type is determined by tags:
- **Multiple Choice** → tag: "Multiple Choice", has 4 choices
- **True/False** → tag: "True/False", has 2 choices
- **Fill in the Blank** → tag: "Fill in the Blank", no choices — ⚠️ correct answer storage TBD (pending content team decision)

---

## Business Rules
- `is_active=False` questions are never included in exam generation
- A question cannot appear twice in the same exam
- Teachers can only see exams belonging to their own organization
- Teachers can only see/edit questions they created (org-scoped), plus all global questions (read-only)
- If not enough questions exist for given constraints, return a user-facing error (do not silently skip)
- `organization` ve `created_by` alanları soru eklenirken view tarafından otomatik set edilir — teacher form'dan seçmez

---

## Exam Generation Logic
Teacher inputs: total question count + per-level min/max percentage ranges + optional tag filters.

Algorithm flow (`exams/services.py`):
1. `_calculate_counts()` — convert ratio inputs into exact per-level question counts
2. `_filter_questions()` — apply level + tag filters; **global sorular (org=None) + teacher'ın org soruları** birlikte havuza alınır:
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
- Login → check role → admin goes to `/admin/`, teacher goes to `/dashboard/`
- Teachers only see their own organization's exams and questions
- Django session auth (no JWT, no API keys)

---

## App Details

### `accounts/`
**Purpose:** User authentication, organization management, role-based routing.

| File | Content |
|------|---------|
| `models.py` | `Organization`, `User` (AbstractUser with role + organization FK; first_name/last_name zorunlu) |
| `views.py` | `login_view`, `logout_view`, `role_redirect_view` |
| `forms.py` | `LoginForm` |
| `mixins.py` | `TeacherRequiredMixin`, `AdminRequiredMixin` |
| `admin.py` | `UserAdmin` (organization + role visible), `OrganizationAdmin` |

---

### `questions/`
**Purpose:** Question bank content management. Global sorular Django admin üzerinden yönetilir. Org'a özel sorular teacher-facing view'lar üzerinden eklenir.

| File | Content |
|------|---------|
| `models.py` | `TagCategory`, `Tag`, `Question` (organization + created_by FK dahil), `Choice` |
| `admin.py` | `ChoiceInline`, `QuestionAdmin` (level/tag/is_active/organization filtreleri), `TagAdmin`, `TagCategoryAdmin` |
| `views.py` | `QuestionListView`, `QuestionCreateView`, `QuestionUpdateView` (sadece teacher erişimli, org-scoped) |
| `forms.py` | `QuestionForm` (organization ve created_by alanları hariç — view'da otomatik set edilir) |

---

### `exams/`
**Purpose:** Exam generation algorithm and exam history.

| File | Content |
|------|---------|
| `models.py` | `Exam` |
| `services.py` | `ExamGeneratorService` — full algorithm, independent from views |
| `views.py` | `ExamCreateView`, `ExamPreviewView`, `ExamHistoryView` |
| `forms.py` | `ExamGenerationForm` (total count, per-level min/max, tag selection) |

---

### `dashboard/`
**Purpose:** Teacher-facing panel. No models — only reads from `exams/`.

| File | Content |
|------|---------|
| `views.py` | `DashboardHomeView` (recent exams + stats), `ProfileView` (read-only profile) |

---

### `core/`
**Purpose:** Shared helpers used across multiple apps. No models, no migrations.

| File | Content |
|------|---------|
| `mixins.py` | `OrgFilterMixin` — filters querysets by `request.user.organization` |
| `context_processors.py` | `user_role_context` — injects `role` into every template context |
| `templatetags/core_tags.py` | `active_nav` — marks active nav link with Bootstrap `active` class |

---

## General Request Flow

```
Browser
  → accounts/      (login, role check)
  → dashboard/     (home, recent exams)
  → questions/     (teacher kendi sorularını ekler/listeler)
  → exams/create   (form: count + level ratios + tag filters)
  → services.py    (ExamGeneratorService: global + org soruları birleşik havuzdan seçer)
  → exams/preview  (generated exam displayed, print button)
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
- No student-facing features (planned for future)
- No CSV/Excel import (planned for future)
- No JWT or token auth
- No frontend framework (Django templates only)

---

## How to Use This File
1. Paste this file at the start of every new chat
2. Update the **Current Status** table to reflect what's done
3. State which app/area you're working on

Examples:
- "accounts app'ini yazıyorum, login_view'ı nasıl yapılandırmalıyım?"
- "ExamGeneratorService'in _calculate_counts metodunu birlikte yazalım."
- "Dashboard'da teacher sadece kendi org sınavlarını görsün, OrgFilterMixin'i nasıl uygularım?"
- "Question admin'inde ChoiceInline'ı nasıl kurarım?"
- "Teacher soru eklerken organization ve created_by otomatik nasıl set edilir?"