# Project Context: English Question Bank System

## What This Is
A Django web application for English language schools. Teachers log in and generate automatic exams from a question bank, then download them as PDF. No public API, no mobile app — web only.

---

## Current Status
> **Update this section at the start of every new chat.**

| App | Status |
|-----|--------|
| `accounts/` | ✅ Done |
| `core/` | ✅ Done |
| `questions/` | ✅ Done (Stage 3) — Stage 9-10 will extend it (new question types, Passage) |
| `exams/` | ✅ Done (Stage 4) — Stage 8, 11, 12 will extend it (shuffle, PDF header, rework, scoring) |
| `dashboard/` | ✅ Done (Stage 5) |
| `org/` | ✅ Done (Stage 6) — Stage 13 will extend it (dashboard stats) |

Statuses: ⬜ Not started · 🔧 In progress · ✅ Done

> **Note:** `students/` app removed from scope. Teachers no longer add questions — contributors do.
> **Note:** Stages 8–13 (see progress3.md) introduce advanced question types (Fill in the Blank, Matching), Passage-based dependent question groups (Reading/Listening), section-based scoring, and PDF/dashboard enhancements. Deploy prep is deferred to the final stage (14).

---

## Tech Stack
- Python 3.12+, Django 5.x, PostgreSQL
- uv (package manager), Docker + Docker Compose
- Bootstrap 5, django-crispy-forms + crispy-bootstrap5
- Pillow, whitenoise, gunicorn, nginx, weasyprint (PDF export)
- Environment variables via `os.environ` (no django-environ)

---

## Four User Roles
**Admin** (internal team) — manages all content via Django admin. Adds global questions, tags, manages organizations and all users.

**Contributor** (content team — e.g. Mali, Buğra) — logs in to a contributor panel. Adds and edits questions (always global, `organization=None`). Cannot manage users or organizations.

**Org Admin** (course owner / department head) — logs in to org panel. Manages their own teachers. Can view all questions accessible to their organization (read-only). Sees exam statistics across their organization.

**Teacher** (client users) — logs in to a custom dashboard. Generates exams and downloads them as PDF. Cannot add or edit questions.

---

## App Structure

```
accounts/    # Custom user model, Organization model, login/logout, role-based redirect
questions/   # Question, Choice, Tag, TagCategory, Passage (Stage 10), MatchingPair (Stage 9) models + admin + contributor-facing views
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
> **Planned (Stage 10):** a "+ Add Passage" entry point in the contributor question UI (no fixed URL decided yet).

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
- **Passage** *(Stage 10)* → `type` (reading/listening), `level` (A1–C2), `text` (reading), `audio`/`audio_label` (listening), `created_by` FK. Represents a shared paragraph or audio clip that multiple questions depend on.
- **Question** → `level` (A1–C2, inherited from `passage.level` when `passage` is set), `text`, `image`, `audio`, `audio_label`, `correct_answer_text` *(Stage 9, Fill in the Blank)*, `is_active`,
  `organization` FK (null=True → global question), `created_by` FK (null=True → added by admin), `passage` FK *(Stage 10, null=True → standalone question if empty)*
- **Choice** → `question` FK, `text`, `is_correct`
- **MatchingPair** *(Stage 9)* → `question` FK, `left_text`, `right_text`

#### Audio field
Questions may include an audio file for listening exercises. `audio` is a `FileField` (upload_to=`questions/audio/`). If present, the exam preview and PDF export show a download link or streaming player. `audio_label` (e.g. "Part 1") is a print-only label, no other function. Teachers cannot add/edit audio — contributors and admin manage it.

#### Question pool logic
| `organization` | `created_by` | Meaning |
|---|---|---|
| `None` | `None` | Global question added by admin |
| `None` | admin/contributor user | Global question added by admin or contributor |
| School A | (admin, via Django admin) | School A specific — contributors never set this themselves |

> Contributors never select `organization` in their form — it is always left unset (`None`), making every contributor-added question global. Only Admin can assign a question to a specific organization, via the Django admin panel.

---

### exams
- **Exam** → `teacher` FK (`on_delete=CASCADE`), `organization` FK (`on_delete=CASCADE`), `parameters` JSONField, `questions` M2M, `created_at`, `name` *(Stage 8, optional, teacher-entered exam title)*
- **TeacherQuestionIndex** → `teacher` FK, `question` FK, `used_at` — tracks which questions a teacher has already received, so the same question is never given to the same teacher twice.

> **on_delete rationale:** both `teacher` and `organization` use `CASCADE` — if a teacher account or an organization is deleted, their exams are deleted with them (no orphaned exam records are kept).

`parameters` JSON example:
```json
{
  "total": 20,
  "levels": {
    "B1": 8,
    "B2": 6,
    "C1": 6
  },
  "tags": [3, 7],
  "scoring": {
    "reading": 5,
    "listening": 3,
    "fill_in_blank": 2
  }
}
```
> Level values are exact question counts entered directly by the teacher (not percentages). The sum of all level counts must equal `total` — enforced live in the UI with JS and re-validated server-side. The `scoring` key is added in Stage 12.

---

## Question Types
All questions use the same model. Type is determined by tags:
- **Multiple Choice** → tag: "Multiple Choice", has 4 choices, choices are shuffled on every render (preview/PDF)
- **True/False** → tag: "True/False", has 2 choices, shuffled on every render
- **Fill in the Blank** *(Stage 9)* → tag: "Fill in the Blank", no choices, correct answer stored in `correct_answer_text`
- **Matching** *(Stage 9)* → tag: "Matching", pairs stored in `MatchingPair`, right-side order shuffled on every render
- **Reading** *(Stage 10)* → tag: "Reading", `passage` FK set to a `Passage` of type `reading`; 3–5 questions share one passage, inherit its level, and always appear consecutively in a generated exam
- **Listening** *(Stage 10)* → tag: "Listening", `passage` FK set to a `Passage` of type `listening`; same grouping/ordering rule as Reading

---

## Business Rules

### Question Rules
- `is_active=False` questions are never included in exam generation
- A question cannot appear twice in the same exam
- **Teachers cannot add or edit questions** — only contributors and admin can
- Contributors can only edit questions they created (`created_by=request.user`)
- Contributors can view global questions (read-only) + questions in their own org (if org-scoped)
- **Future consideration:** currently `QuestionListView.get_queryset()` restricts every contributor to only their own questions (`filter(created_by=request.user)`). If later some contributors need to see all questions (e.g. a senior contributor/editor role), add a `can_view_all_questions` BooleanField to `User` and branch in `get_queryset()` accordingly — this is a small, isolated change since the restriction lives in one place.
- Org Admins can view all questions accessible to their organization (read-only in the org panel)
- `created_by` is set automatically by the view; `organization` is never set by the contributor-facing form (always stays `None`)
- **(Stage 10)** A passage's `level` is inherited by all of its child questions — a passage's questions are never counted as a separate pool, they count toward the same per-level totals as standalone questions.

### Exam Rules
- Teachers can only see exams they generated (filtered by `teacher=request.user`)
- Org Admins can see all exams within their organization
- If not enough questions exist for given constraints, return a user-facing error (do not silently skip)
- **Teacher Question Index:** when generating an exam, questions already in a teacher's index are excluded first. After generation, all selected questions are added to that teacher's index. This prevents the same question from appearing in a later exam for the same teacher.
- **(Stage 8)** Choice order (and Matching right-column order, once Stage 9 lands) is re-randomized every time an exam is rendered — it is *not* fixed at generation time, so preview and PDF may show different orders on separate views.
- **(Stage 11)** Questions belonging to the same `Passage` always appear consecutively in the final exam — a passage group is never interrupted by other questions once it starts. Partial selection from a passage's question pool is allowed (e.g. 3 of its 5 questions).
- **(Stage 12)** Each section type (Multiple Choice, True/False, Fill in the Blank, Matching, Reading, Listening) has its own point value per question; the total across the whole exam must equal 100, enforced live in the UI and re-validated server-side.

### Org Admin Rules
- Org Admins can add teachers to their own organization only
- Org Admins cannot add other Org Admins (only Admin can do that)
- Org Admins cannot access other organizations' data

---

## Exam Generation Logic
Teacher inputs: total question count + exact per-level question counts (must sum to total) + optional tag filters. *(Stage 11 adds Reading/Listening passage-count and questions-per-passage inputs; Stage 12 adds per-section point values.)*

Algorithm flow (`exams/services.py`):
1. `_calculate_counts()` — validate that per-level counts sum to the total (counts are already exact, entered directly by the teacher; no percentage-to-count conversion needed)
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

> **Passage-aware sampling (Stage 11):** independent questions and passage-linked question groups (Reading/Listening) are drawn from separate pools but count toward the same per-level totals, since a passage's level is inherited by all its questions. Once a passage group is selected, all of its sampled questions stay consecutive in the final exam order — they are never interleaved with other questions mid-group. Partial selection from a passage is allowed (e.g. 3 of its 5 questions).

> **Choice shuffling (Stage 8):** choice order (and Matching right-column order, Stage 9) is re-randomized on every render of `ExamPreviewView` and `ExamDownloadView` — computed once per request and reused between the two so a single view of the exam is internally consistent, but two separate requests (e.g. preview then download) may show different orders.

---

## PDF Export
After generating an exam, teachers can download it as a PDF:
- Rendered via `exams/pdf.html`, a standalone template (does not extend `base.html`) processed by weasyprint
- Questions and choices are rendered into a clean printable layout, numbered, with lettered choices (via the `to_letter` filter)
- Includes an answer key page (page-break before it)
- If a question has an `audio` file, the PDF shows a QR code or short URL linking to the audio file (teachers cannot embed audio in PDF)
- **(Stage 8)** Header layout: course name (`exam.organization.name`) centered at the top, exam name (if set) directly below it, and blank "Student Name / Date / Score" lines on the right for hand-filling (no student records exist in the system)
- **(Stage 9)** Fill in the Blank questions render a blank/underlined line instead of choices; Matching questions render as two columns (numbered left, shuffled-lettered right)
- **(Stage 12)** Each question shows its point value alongside the question text
- Implemented in `exams/views.py` as `ExamDownloadView` using weasyprint

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

---

### `questions/`
**Purpose:** Question bank content management. Global questions managed via Django admin or contributor panel. All contributor-added questions are global.

| File | Content |
|------|---------|
| `models.py` | `TagCategory`, `Tag`, `Question` (organization + created_by FK, audio/audio_label, `correct_answer_text` from Stage 9, `passage` FK from Stage 10), `Choice`, `MatchingPair` (Stage 9), `Passage` (Stage 10) |
| `admin.py` | `ChoiceInline`, `QuestionAdmin` (level/tag/is_active/organization filters), `TagAdmin`, `TagCategoryAdmin` |
| `views.py` | `QuestionListView`, `QuestionCreateView`, `QuestionUpdateView` (contributor-only, own questions only) |
| `forms.py` | `QuestionForm`, `ChoiceForm`, `ChoiceFormSet` (organization and created_by excluded — created_by set automatically, organization always left unset) |

> **Stage 9 adds:** `MatchingPairFormSet`, conditional JS-driven form switching between choices / fill-in-the-blank field / matching formset based on selected tag.
> **Stage 10 adds:** `Passage` create flow, "+ Add Passage" entry point, grouped display in `QuestionListView`.

---

### `exams/`
**Purpose:** Exam generation algorithm, exam history, and PDF download.

| File | Content |
|------|---------|
| `models.py` | `Exam` (adds `name` in Stage 8), `TeacherQuestionIndex` |
| `services.py` | `ExamGeneratorService` — full algorithm including index update; Stage 11 adds passage-aware sampling |
| `views.py` | `ExamCreateView`, `ExamPreviewView`, `ExamDownloadView` (PDF, weasyprint), `ExamHistoryView` |
| `forms.py` | `ExamGenerationForm` (total count, exact per-level question counts, tag selection; Stage 8 adds exam name; Stage 11 adds passage-count fields; Stage 12 adds per-section scoring) |

---

### `dashboard/`
**Purpose:** Teacher-facing panel. No models — only reads from `exams/`.

| File | Content |
|------|---------|
| `views.py` | `DashboardHomeView` (recent exams + stats), `ProfileView` (read-only profile) |

---

### `org/`
**Purpose:** Org Admin panel. No models — reads from `accounts/`, `questions/`, `exams/`.

| File | Content |
|------|---------|
| `views.py` | `OrgDashboardView`, `TeacherListView`, `TeacherCreateView`, `TeacherDetailView`, `OrgQuestionListView`, `OrgExamListView` |
| `forms.py` | `TeacherCreateForm` (creates a User with role=teacher, same organization as org_admin) |

> **Stage 13 adds:** additional pool breakdown stats on `OrgDashboardView` — passage count, listening clip count, per-type question counts, total pool size. View-layer only, no schema changes.

---

### `core/`
**Purpose:** Shared helpers used across multiple apps. No models, no migrations.

| File | Content |
|------|---------|
| `apps.py` | to be able to add INSTALLED_APPS in config/settings |
| `mixins.py` | `OrgFilterMixin` — filters querysets by `request.user.organization` |
| `context_processors.py` | `user_role_context` — injects `role` into every template context |
| `templatetags/__init__.py` | empty file, to define as python package |
| `templatetags/core_tags.py` | `active_nav` — marks active nav link with Bootstrap `active` class; `to_letter` — converts 1→A, 2→B... for choice/answer-key lettering |

---

## General Request Flow

```
Browser
  → accounts/        (login, role check)
  ↓
  ├── /admin/        (Admin — manages everything)
  │
  ├── /questions/    (Contributor — adds/edits questions, manages audio, Passage in Stage 10)
  │
  ├── /org/          (Org Admin — manages teachers, views questions/exams)
  │
  └── /dashboard/    (Teacher — creates exams, downloads PDF)
        → exams/create    (form: count + level counts + tag filters, name in Stage 8, passages in Stage 11, scoring in Stage 12)
        → services.py     (ExamGeneratorService: global + org questions, excludes teacher's index, passage-aware from Stage 11)
        → exams/preview   (generated exam displayed, choices shuffled each render)
        → exams/download  (PDF export, audio linked via QR/URL, header/answer key/scoring)
```

---

## Settings Structure
```
settings/
  base.py        # shared config
  local.py       # DEBUG=True, local DB
  production.py  # DEBUG=False, real SECRET_KEY, allowed hosts, DATABASE_URL parsing
```

---

## Deployment Notes
- `Dockerfile` installs weasyprint's system dependencies (`libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf-2.0-0`, `libffi-dev`, `shared-mime-info`, `fonts-liberation`) before `uv sync`.
- `entrypoint.sh` runs `migrate`, `collectstatic`, a conditional non-interactive superuser creation (via `DJANGO_SUPERUSER_*` env vars, checked against existing users to avoid duplicate-creation errors), then starts `gunicorn`.
- Deploy prep (production settings, hosting config, final checks) is intentionally the **last** stage (14) — all new features (Stages 8–13) are built first.

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
- "Stage 8'deki şık karıştırmayı ExamPreviewView'a nasıl ekleriz?"
- "Passage modelini questions/models.py'ye nasıl ekleyelim?"
- "_sample_questions() içinde passage gruplarını ardışık tutmak için nasıl bir mantık kurmalıyız?"
- "Section bazlı puanlamayı ExamGenerationForm'a nasıl ekleriz?"
- "OrgDashboardView'a passage/listening sayacı nasıl eklerim?"

---

## Notes
### Permissions (Sonraya Bırakıldı)
- `role=teacher` kaydedilince teacher izinleri otomatik atanacak
- `role=org_admin` kaydedilince org_admin izinleri otomatik atanacak
- `role=contributor` kaydedilince contributor izinleri otomatik atanacak
- Elle seçim yapılmayacak — signal veya `save()` override ile çözülecek
- Mixin'ler tamamlandıktan sonra hangi izinlerin gerekli olduğu netleşecek

### Stage 11 Öncesi Netleşmesi Gereken Nokta
- Bir passage'ın soruları, kısmi seçim durumunda (örn. 5 sorudan 3'ü seçildiğinde) kendi aralarında karışsın mı, yoksa sabit bir sırada mı kalsın? Sadece "paragraflar arası ardışıklık kırılmaz" netleşti, grup içi sıralamanın kendisi henüz netleşmedi.
