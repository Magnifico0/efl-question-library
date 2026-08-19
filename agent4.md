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
| `questions/` | 🔧 In progress — Stage 3 done, Stage 9 (Fill in the Blank/Matching) done, **Stage 9.5 (Section/Type refactor) next**, then Stage 10 (Passage) |
| `exams/` | ✅ Done (Stage 4) — Stage 8 done (shuffle, PDF header). Stage 11 in progress — passage-aware generation rebuilt around per-level passage counts (see Stage 11 REVISED below), Stage 12 pending |
| `dashboard/` | ✅ Done (Stage 5) |
| `org/` | ✅ Done (Stage 6) — Stage 13 will extend it (pool breakdown stats) |

Statuses: ⬜ Not started · 🔧 In progress · ✅ Done

> **Note:** `students/` app removed from scope. Teachers no longer add questions — contributors do.
> **Note:** Stage 9.5 is a new stage, inserted between Stage 9 and Stage 10, after a design review. It replaces the old "tag decides everything" approach with two explicit model fields (`question_type`, `section`) before Passage is built on top of it. See "Design Decision Log" below for the reasoning.

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
questions/   # Question, Choice, Tag, TagCategory, MatchingPair, Passage (Stage 10) models + admin + contributor-facing views
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
| `/questions/passages/<id>/` *(Stage 10)* | `PassageDetailView` | questions | Contributor (own only) |
| `/org/` | `OrgDashboardView` | org | Org Admin |
| `/org/teachers/` | `TeacherListView` | org | Org Admin |
| `/org/teachers/add/` | `TeacherCreateView` | org | Org Admin |
| `/org/teachers/<id>/` | `TeacherDetailView` | org | Org Admin |
| `/org/questions/` | `OrgQuestionListView` | org | Org Admin |
| `/org/exams/` | `OrgExamListView` | org | Org Admin |
| `/admin/` | Django admin | — | Admin (you) |

> **Removed:** `/students/` URLs — student tracking is out of scope.
> **Planned (Stage 10):** `QuestionCreateView` accepts an optional `?passage=<id>` query param — when present, the form is rendered in "attached to passage" mode (see Passage section below). No separate URL needed for this.

---

## Core Models

### accounts
- **Organization** → `name`, `slug`, `created_at`
- **User** (AbstractUser) → `role` (admin/org_admin/contributor/teacher), `organization` FK
  - `first_name` and `last_name` → inherited from AbstractUser, required (`blank=False`)
  - Used to display question ownership (`created_by.get_full_name()`)

### questions
- **TagCategory** → `name` (e.g. Grammar, Vocabulary, Topic/Theme). Purely for content classification — no longer used to drive form/PDF behavior (see Stage 9.5).
- **Tag** → `name`, `category` FK. Example: Grammar → Tenses, Conditionals, Modals; Vocabulary → Idioms, Phrasal Verbs; Topic/Theme → Travel, Business, Health.
- **Question** →
  - `question_type` *(Stage 9.5)* → `CharField(choices=[mc, tf, fib, matching, open_ended])` — determines how the question is rendered and what related data it has.
  - `section` *(Stage 9.5)* → `CharField(choices=[general, reading, listening, writing, speaking])` — determines which skill/section the question belongs to, independent of `question_type`.
  - `level` (A1–C2, inherited from `passage.level` when `passage` is set)
  - `text` — question text, or the prompt/topic for `open_ended` questions
  - `image`, `audio`, `audio_label`, `is_active`
  - `correct_answer_text` *(Stage 9, used when `question_type=fib`)*
  - `word_count_instruction` *(Stage 9.5, used when `question_type=open_ended`)* — free-text instruction, e.g. "Write at least 150 words", no correct answer stored
  - `organization` FK (null=True → global question), `created_by` FK (null=True → added by admin)
  - `passage` FK *(Stage 10, null=True → standalone question if empty)*
- **Choice** → `question` FK, `text`, `is_correct` (used when `question_type` is `mc` or `tf`)
- **MatchingPair** *(Stage 9)* → `question` FK, `left_text`, `right_text` (used when `question_type=matching`)
- **Passage** *(Stage 10)* → `kind` (reading/listening), `level` (A1–C2), `text` (reading), `audio`/`audio_label` (listening), `image`/`image_label`, `created_by` FK. Represents a shared paragraph or audio clip that one or more questions depend on. `level` exists specifically to make passage selection level-aware — see Stage 11 REVISED in the Design Decision Log for why.

> **`question_type` and `section` are independent axes.** `question_type` decides *how a question is rendered* (choices vs. blank line vs. matching columns vs. open writing space). `section` decides *which skill it belongs to* and whether it's tied to a `Passage`. Any combination of the two is valid — e.g. a Reading-section question can be Multiple Choice, True/False, Fill in the Blank, or Matching; a `general`-section question can be any of the same four types. `open_ended` is only used by `writing`/`speaking` sections.

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
  "reading_levels": {
    "B1": 3,
    "B2": 2
  },
  "listening_levels": {
    "C1": 2
  },
  "scoring": {
    "reading": 5,
    "listening": 3,
    "fill_in_blank": 2
  }
}
```
> Level values are exact question counts entered directly by the teacher (not percentages). The sum of all level counts must equal `total` — enforced live in the UI with JS and re-validated server-side. `reading_levels` / `listening_levels` *(Stage 11 REVISED)* are a **subset** of `levels` — for each level, `reading_levels[L] + listening_levels[L]` must not exceed `levels[L]`; the remainder for that level is drawn from standalone/writing/speaking questions. There is no `passage_count` field — how many distinct passages are used per level is decided automatically by the generation algorithm. The `scoring` key is added in Stage 12.

---

## Question Types & Sections (Stage 9.5 model)

Two independent fields on `Question`, replacing the old "one tag decides everything" approach:

### `question_type` — how the question is rendered
| Value | Meaning | Related data | Has answer key? |
|---|---|---|---|
| `mc` | Multiple Choice | 4 `Choice` rows, shuffled every render | Yes |
| `tf` | True/False | 2 `Choice` rows, shuffled every render | Yes |
| `fib` | Fill in the Blank | `correct_answer_text` | Yes |
| `matching` | Matching | `MatchingPair` rows, right column shuffled every render | Yes |
| `open_ended` | Writing/Speaking prompt | `word_count_instruction` (optional) | No — free response, not auto-scored |

### `section` — which skill the question belongs to
| Value | Passage required? | Typical `question_type` | Controlled by `ENABLED_SECTIONS`? |
|---|---|---|---|
| `general` | No | mc / tf / fib / matching | Always on |
| `reading` | Yes (`Passage.type=reading`) | mc / tf / fib / matching | Always on |
| `listening` | Yes (`Passage.type=listening`) | mc / tf / fib / matching | Always on |
| `writing` | No | open_ended | Configurable |
| `speaking` | No | open_ended | Configurable |

`general` is the section for standalone questions with no shared passage — i.e. ordinary grammar/vocabulary questions that used to have no section concept at all before Stage 9.5.

### Section visibility toggle (`ENABLED_SECTIONS`)
Speaking is a section the team is not 100% committed to long-term (pending a decision with a colleague). Rather than removing it later — which would mean deleting a model field and losing content — it is built now but made toggle-able:

```python
# settings/base.py
ENABLED_SECTIONS = ["general", "reading", "listening", "writing", "speaking"]
```

- A `core` context processor exposes `enabled_sections` to every template.
- `QuestionForm`'s `section` field choices are filtered to `ENABLED_SECTIONS`.
- `QuestionListView`, `ExamGenerationForm`, and any section-picker UI filter by `section__in=settings.ENABLED_SECTIONS`.
- If Speaking is later disabled by removing it from the list, **existing Speaking questions stay in the database untouched** — they simply stop appearing in contributor/teacher/org_admin UI and stop being selectable for new exams. Re-enabling it (adding it back to the list) restores full visibility with zero data loss and zero migration needed.

---

## Passage Model (Stage 10)

A `Passage` represents a shared paragraph (Reading) or audio clip (Listening) that one or more questions are attached to via `Question.passage`.

**Key design decision:** there is **no fixed number of sub-questions** per passage, and **no upfront "how many questions?" input**. The flow is:

1. Contributor creates a `Passage` (type, level, text or audio).
2. This opens a `PassageDetailView` — shows the passage content plus a list of its questions (empty at first) and a **"+ Add Question"** button.
3. Each click on "+ Add Question" opens the normal question form (`QuestionCreateView`) with `?passage=<id>` in the URL. The passage's `level` is shown read-only and cannot be changed on this question; `section` is pre-set to `reading`/`listening` and locked. `question_type` (MC / True-False / Fill in the Blank / Matching) remains freely selectable — **a single passage can mix question types**, e.g. two Multiple Choice questions and one Matching question under the same paragraph.
4. A passage can have as few as **one** question. There is no min/max enforced at the model or form level.
5. Editing an existing passage-linked question works the same as any other question edit, except `level`/`section`/`passage` stay locked to what the passage dictates.

This keeps passage creation lightweight (no formset, no "declare N questions upfront" step) and mirrors how a real content writer works — write the paragraph, then add as many comprehension questions as make sense, one at a time.

`QuestionListView` groups standalone (`passage=None`) questions separately from passage-linked ones; passage-linked questions are shown nested under their passage's title.

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
- **(Stage 9.5)** `question_type` and `section` are independent fields — any combination is valid except `open_ended`, which is only used by `writing`/`speaking`.
- **(Stage 10)** A passage's `level` and `section` are inherited by all of its child questions and are read-only on the question form once a passage is attached — a passage's questions are never counted as a separate pool, they count toward the same per-level totals as standalone questions. A passage may have any number of questions (including just one), added one at a time via "+ Add Question" — there is no fixed or upfront question count.

### Exam Rules
- Teachers can only see exams they generated (filtered by `teacher=request.user`)
- Org Admins can see all exams within their organization
- If not enough questions exist for given constraints, return a user-facing error (do not silently skip)
- **Teacher Question Index:** when generating an exam, questions already in a teacher's index are excluded first. After generation, all selected questions are added to that teacher's index. This prevents the same question from appearing in a later exam for the same teacher.
- **(Stage 8)** Choice order (and Matching right-column order, once Stage 9 lands) is re-randomized every time an exam is rendered — it is *not* fixed at generation time, so preview and PDF may show different orders on separate views.
- **(Stage 11)** Questions belonging to the same `Passage` always appear consecutively in the final exam — a passage group is never interrupted by other questions once it starts. Partial selection from a passage's question pool is allowed (e.g. 2 of its 4 questions), and questions within a partially-selected group may be shuffled among themselves (open question, to be confirmed during Stage 11 design — see Notes).
- **(Stage 12)** Each section type (general MC/TF/FIB/Matching, Reading, Listening, Writing, Speaking) has its own point value per question; the total across the whole exam must equal 100, enforced live in the UI and re-validated server-side. `writing`/`speaking` (open_ended) questions are scored manually by the teacher — the system just reserves their point allocation, it does not grade them.

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

> **Passage-aware sampling (Stage 11):** independent questions and passage-linked question groups (Reading/Listening) are drawn from separate pools but count toward the same per-level totals, since a passage's level is inherited by all its questions. Once a passage group is selected, all of its sampled questions stay consecutive in the final exam order — they are never interleaved with other questions mid-group. Partial selection from a passage is allowed.

> **Choice shuffling (Stage 8):** choice order (and Matching right-column order, Stage 9) is re-randomized on every render of `ExamPreviewView` and `ExamDownloadView` — computed once per request and reused between the two so a single view of the exam is internally consistent, but two separate requests (e.g. preview then download) may show different orders.

---

## PDF Export
After generating an exam, teachers can download it as a PDF:
- Rendered via `exams/pdf.html`, a standalone template (does not extend `base.html`) processed by weasyprint
- Rendering now branches on `question.question_type` (not on tag names — see Stage 9.5):
  - `mc` / `tf` → lettered choices via the `to_letter` filter
  - `fib` → a blank/underlined line instead of choices
  - `matching` → two columns (numbered left, shuffled-lettered right)
  - `open_ended` → the prompt text, `word_count_instruction` if set, and blank ruled lines for the student to write on; excluded from the answer key page entirely
- Includes an answer key page (page-break before it) — `open_ended` questions are skipped on this page since there is no single correct answer
- If a question has an `audio` file, the PDF shows a QR code or short URL linking to the audio file (teachers cannot embed audio in PDF)
- **(Stage 8)** Header layout: course name (`exam.organization.name`) centered at the top, exam name (if set) directly below it, and blank "Student Name / Date / Score" lines on the right for hand-filling (no student records exist in the system)
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
| `models.py` | `TagCategory`, `Tag` (content classification only, Stage 9.5), `Question` (`question_type`, `section`, `word_count_instruction` from Stage 9.5; organization + created_by FK; audio/audio_label; `correct_answer_text` from Stage 9; `passage` FK from Stage 10), `Choice`, `MatchingPair` (Stage 9), `Passage` (Stage 10) |
| `admin.py` | `ChoiceInline`, `QuestionAdmin` (level/section/question_type/is_active/organization filters), `TagAdmin`, `TagCategoryAdmin` |
| `views.py` | `QuestionListView`, `QuestionCreateView` (branches on `?passage=<id>` query param), `QuestionUpdateView`, `PassageDetailView` (Stage 10) — all contributor-only, own content only |
| `forms.py` | `QuestionForm` (`section` + `question_type` as two independent dropdowns; JS shows/hides Choices / Fill-in-the-Blank field / Matching formset / open-ended fields based on `question_type`, not tags), `ChoiceForm`, `ChoiceFormSet` (organization and created_by excluded — created_by set automatically, organization always left unset) |

> **Stage 9.5 adds:** `question_type` and `section` CharFields on `Question`, data migration from old "Fill in the Blank"/"Matching" tags into `question_type`, `ENABLED_SECTIONS` setting + context processor, form/PDF rendering switched from tag-based to field-based branching.
> **Stage 10 adds:** `Passage` model, `PassageDetailView` with "+ Add Question" flow (no upfront question count), grouped display in `QuestionListView`.

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

> **Stage 13 adds:** additional pool breakdown stats on `OrgDashboardView` — per-section counts (general/reading/listening/writing/speaking), passage count, listening clip count, total pool size. View-layer only, no schema changes.

---

### `core/`
**Purpose:** Shared helpers used across multiple apps. No models, no migrations.

| File | Content |
|------|---------|
| `apps.py` | to be able to add INSTALLED_APPS in config/settings |
| `mixins.py` | `OrgFilterMixin` — filters querysets by `request.user.organization` |
| `context_processors.py` | `user_role_context` — injects `role` into every template context. `enabled_sections` *(Stage 9.5)* — injects `settings.ENABLED_SECTIONS` into every template |
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
  base.py        # shared config, ENABLED_SECTIONS (Stage 9.5)
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
- No auto-grading for `open_ended` (writing/speaking) questions — teacher grades by hand, system only reserves the point allocation

---

## Design Decision Log

### Why Stage 9.5 exists (Section/Type refactor)
Originally, "question type" (Multiple Choice, Fill in the Blank, Matching) and "section" (Reading, Listening, Speaking) were both expressed as `Tag` objects in the same M2M field. This had two problems:
1. **No mutual exclusion.** Nothing stopped a question from being tagged both "Speaking" and "Reading" at once — the constraint lived only in ad-hoc JS/view logic reading tag names as strings, which is fragile.
2. **Stage 12 (section-based scoring) already assumes a clean section concept** (`"scoring": {"reading": 5, "listening": 3, ...}`). Deriving that from tag name strings later would require a messy parsing layer.

The fix: `question_type` and `section` became real model fields (`CharField` with `choices`), independent of each other and independent of `Tag`. `Tag`/`TagCategory` are now used purely for content classification (Grammar → Tenses, Vocabulary → Idioms, Topic/Theme → Travel, etc.) and no longer drive any form or rendering logic.

### Why Passage has no fixed question count
Originally planned as "3–5 sub-questions per passage" with a formset-driven flow (declare N questions upfront, fill them all in one form). This was reconsidered: a passage can reasonably have just one question, and different sub-questions under the same passage can be different `question_type`s (e.g. 2 Multiple Choice + 1 Matching under one reading passage). The simpler and more flexible flow is a `PassageDetailView` with a "+ Add Question" button that opens the normal single-question form each time, pre-locking `level`/`section` to the passage's values. No formset, no upfront count, no artificial min/max.

### Why Speaking is built but toggle-able
Whether the school will keep a Speaking section long-term is not settled (pending discussion). Rather than leaving it out and doing a risky removal later, or building it in a way that's hard to undo, it's included in the model now but gated by `settings.ENABLED_SECTIONS`. Removing it from that list hides it from every contributor/teacher/org_admin-facing view without touching the database — existing Speaking questions and any exams that used them stay intact, unaffected, and simply invisible until re-enabled.


### Why `Exam.questions` was migrated to a `through` model
Passage-linked questions must appear consecutively (unbroken) in the exam output (Stage 11). A plain M2M field cannot guarantee question order at the database level. Two options were considered:
1. `through` model (`ExamQuestion` + `order` field) — order guaranteed at the DB level, `exam.questions.all()` comes back in the correct order automatically
2. Storing order inside `Exam.parameters` JSON — no migration needed, but manual sorting code would have to be repeated in every view

`through` was chosen because: (a) the project isn't in production yet, so the migration risk is near-zero right now — this same migration would be far more costly once real exam data has accumulated; (b) it requires zero extra code in the views, since `Meta.ordering` makes the read side work automatically; (c) if a future feature ever needs "teacher manually reorders questions," the `order` field already provides the foundation for it.

**Note:** Django does not support converting an existing M2M field into a `through`-based one in a single migration (`ValueError: cannot alter to or from M2M fields`). The migration had to be split into two steps: first the field was removed, then re-added with `through`.

### Why Passage question count has a "fixed mode / flexible mode" split — SUPERSEDED, see "Stage 11 REVISED" below
The first design only had "exactly N questions per passage" (`reading_questions_per_passage`). This created an unrealistic constraint: if the pool had 1 passage with 2 questions and 1 passage with 3 questions, a total of 5 usable questions existed, but a strict "3 per passage" rule would reject the 2-question passage outright. Instead, two modes were added:
- **Fixed mode** (`questions_per_passage` filled in): exactly that many questions from each passage — for teachers who want symmetry across passages
- **Flexible mode** (`total_questions` filled in): only the total count matters, distribution across passages is left to the system

The two cannot be filled in at the same time (enforced in `clean()` via the `_validate_passage_section()` helper).

> **This entire fixed/flexible split was removed** once Passage gained a `level` field and a real bug surfaced (see "Stage 11 REVISED" below) — kept here only for history, do not implement this version.

### Stage 11 REVISED — Passage sampling became level-based, "fixed/flexible mode" and `passage_count` removed
After Stage 11 first shipped, `Passage` had no `level` field of its own — the exam form only had flat `reading_passage_count` / `reading_questions_per_passage` / `reading_questions_total` inputs, with no level breakdown for passage-sourced questions. This produced a real bug: requesting e.g. "2 passages, 4 questions total" could silently return 6 questions, because the passage-selection code path and the level-count-validation code path each ran their own independent `random.sample()`/allocation pass — two different random draws that were never guaranteed to agree with each other.

The fix had two parts:
1. **`Passage.level` was added.** Without it, passage-derived questions had no anchor to the same per-level quota (`levels` in `Exam.parameters`) that standalone questions use — there was no way to say "this passage's questions count toward the B1 quota."
2. **`reading_questions_per_passage` / `reading_questions_total` / `reading_passage_count` (and the `listening_*` equivalents) were all removed**, replaced by `reading_levels` / `listening_levels` — per-level dicts, structurally identical to the top-level `levels` dict (see `parameters` JSON example above). The old "fixed mode / flexible mode" split is gone entirely; there is no longer a way to request "exactly N questions per passage," because mixing that with a level-based target created an ambiguous question (which level "bucket" does a fixed-size passage draw count against?).
3. **`passage_count` (how many distinct passages to use) was removed as a teacher-facing input.** The generation algorithm now decides internally how many distinct passages are needed to cover each level's requested count — it consumes shuffled candidate passages one at a time until the level target is met. This was a deliberate simplicity trade-off: a per-passage-level breakdown (e.g. "Passage 1 → A1 → 3 questions, Passage 2 → A2 → 2 questions" as fully separate, individually named inputs) was considered and rejected as unnecessary complexity for what the school actually needs — level-based totals are enough; which specific passages fulfill them doesn't need to be a teacher decision.

**Why this couldn't just reuse the same code as independent (standalone) question sampling:** standalone sampling is a single-layer operation (filter a flat `Question` queryset by level, then `random.sample`). Passage sampling is necessarily two-layered — first choose which `Passage` objects to draw from (each with its own level and its own question-count capacity), then decide how many questions to take from each chosen passage, such that the per-passage takes sum to the requested per-level target without ever splitting a passage's chosen questions apart in the final exam order. That "partition a target count across capacity-limited groups, then keep each group contiguous" problem doesn't exist for standalone questions, so the same function can't be reused as-is. The two paths do now share the same *shape* of logic (shuffle candidates once, consume greedily, validate against the same shuffled list used for selection) to avoid the original bug's root cause — two independent random draws that could disagree.

### Why insufficient passages/questions does not silently fall back to "best available"
Discussed: should the system silently narrow the request and say "couldn't fully satisfy this, here's the best combination I found"? Decided against it — the existing `_validate_counts()` philosophy already favors "raise a clear error if insufficient, let the teacher decide" (the level-based check works the same way). A silent automatic fallback risks a teacher getting a less varied exam than expected (fewer passages, fewer questions) and only noticing after printing/distributing the PDF to students. Instead, the error message states the real capacity of existing passages explicitly (e.g. "at most X questions can be provided — reduce the passage count or the requested question count").
---

## How to Use This File
1. Paste this file at the start of every new chat
2. Update the **Current Status** table to reflect what's done
3. State which app/area you're working on

## Example run command
- `docker compose exec web uv run python manage.py check`

## Examples
- "Stage 9.5'teki question_type/section refactor'ünü Question modeline nasıl ekleriz?"
- "Eski Fill in the Blank / Matching tag'lerinden question_type'a data migration nasıl yazılır?"
- "PassageDetailView'daki '+ Soru Ekle' akışını QuestionCreateView'a nasıl bağlarız?"
- "ENABLED_SECTIONS listesinden speaking'i çıkarınca hangi view'lar etkilenir?"
- "_sample_questions() içinde passage gruplarını ardışık tutmak için nasıl bir mantık kurmalıyız?"
- "Section bazlı puanlamayı ExamGenerationForm'a nasıl ekleriz?"

---

## Notes
- CSV import yazılırken: bulk_create() kullanma, satır satır Model(...) → full_clean() → save() pattern'i kullan. Choice/MatchingPair modellerine, question.question_type ile tutarlılığı kontrol eden clean() metodları eklenmeli (DB trigger'a gerek yok, application-level validation yeterli — tek giriş noktası Django ORM olduğu sürece).
### Permissions (Sonraya Bırakıldı)
- `role=teacher` kaydedilince teacher izinleri otomatik atanacak
- `role=org_admin` kaydedilince org_admin izinleri otomatik atanacak
- `role=contributor` kaydedilince contributor izinleri otomatik atanacak
- Elle seçim yapılmayacak — signal veya `save()` override ile çözülecek
- Mixin'ler tamamlandıktan sonra hangi izinlerin gerekli olduğu netleşecek

### Stage 11 Öncesi Netleşmesi Gereken Nokta
- Bir passage'ın soruları, kısmi seçim durumunda (örn. 4 sorudan 2'si seçildiğinde) kendi aralarında karışsın mı, yoksa sabit bir sırada mı kalsın? Sadece "paragraflar arası ardışıklık kırılmaz" netleşti, grup içi sıralamanın kendisi henüz netleşmedi.

### Speaking Kararı (Beklemede)
- Speaking section'ının projede kalıcı olarak tutulup tutulmayacağı ekip arkadaşıyla henüz netleşmedi. Şimdilik `ENABLED_SECTIONS` listesinde açık tutuluyor; karar netleşince listeden çıkarılıp çıkarılmayacağına karar verilecek — model/migration değişikliği gerekmeyecek.