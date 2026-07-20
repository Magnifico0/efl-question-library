# Build Progress — English Question Bank System

> Check off each step as you complete it: `[ ]` → `[x]`
> Paste this file together with agent2.md at the start of every new chat.

---

## Why This Order?

```
Project setup
  → accounts/       (everything depends on User, must come first)
    → core/         (mixins depend on accounts)
      → questions/  (question bank, requires User + Org)
        → exams/    (requires questions + accounts)
          → dashboard/  (reads from exams/, comes last)
            → org/      (reads from everything, comes last)
              → Polish  (templates, static, deploy)
```

> **Note:** `students/` app removed from build order — student tracking is out of scope.

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
  - `role` → `CharField(choices=[admin, org_admin, contributor, teacher])` ← **contributor eklendi**
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `first_name` and `last_name` → override with `blank=False` (required)
- [x] Add `AUTH_USER_MODEL = 'accounts.User'` to `settings/base.py`
- [x] Create and apply migration — **must be done before any other migrations**

> **⚠️ Güncelleme gerekiyor:** `role` choices'a `contributor` eklenmeli ve migration uygulanmalı. Eğer mevcut migration'da sadece 3 role varsa, yeni bir migration oluştur.

### 1.2 Admin
- [x] Write `OrganizationAdmin`
- [x] Write `UserAdmin`: `role`, `organization`, `first_name`, `last_name` visible

### 1.3 Auth Views
- [x] Write `LoginForm` (`forms.py`)
- [x] Write `login_view`: POST → role check → admin to `/admin/`, org_admin to `/org/`, contributor to `/questions/`, teacher to `/dashboard/`  ← **contributor redirect eklendi**
- [x] Write `logout_view`
- [x] Write `role_redirect_view` (redirect already logged-in users to correct page)
- [x] Wire up URLs: `/login/`, `/logout/`

### 1.4 Mixins
- [x] Write `TeacherRequiredMixin`
- [x] Write `OrgAdminRequiredMixin`
- [x] Write `AdminRequiredMixin`
- [ ] Write `ContributorRequiredMixin` ← **yeni, eklenmeli**

### 1.5 Template
- [x] Write `templates/accounts/login.html` (Bootstrap 5)

**Check:** Login as admin, org_admin, contributor, and teacher — each redirects to the correct page. Visiting `/dashboard/` without login redirects to `/login/`.

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
  - `audio` → `FileField(upload_to='questions/audio/', null=True, blank=True)` ← **yeni, eklenmeli**
  - `tags` → M2M (Tag)
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `created_by` → `ForeignKey(User, null=True, blank=True)`
- [x] Write `Choice` model: `question` FK, `text`, `is_correct`
- [x] Create and apply migration

> **⚠️ Güncelleme gerekiyor:** `audio` alanı Question modeline eklenmeli ve yeni migration oluşturulmalı.

### 3.2 Admin (Global Questions)
- [x] Write `ChoiceInline` (inline choice entry inside Question admin)
- [x] Write `QuestionAdmin`: level / tag / is_active / organization filters
- [x] Write `TagAdmin` and `TagCategoryAdmin`
- [x] Add a few sample questions via admin (for testing)

### 3.3 Contributor-Facing Views
> **Değişiklik:** Bu view'lar artık `ContributorRequiredMixin` kullanıyor. Teacher'lar bu URL'lere erişemiyor.

- [x] Write `QuestionForm`: `organization` and `created_by` fields **not in form**; `audio` field included
- [x] Write `ChoiceForm` and `ChoiceFormSet`: inline choice entry for contributor-facing question form
- [x] Write `QuestionListView`: only questions where `created_by=request.user` — **ContributorRequiredMixin**
- [x] Write `QuestionCreateView`:
  - Set `organization` and `created_by` automatically in `form_valid()`
  - Use `ContributorRequiredMixin` ← **TeacherRequiredMixin'den değiştirildi**
  - Handle `ChoiceFormSet` inline (min 2 choices required for MC/TF; Fill in the Blank and Listening can have no choices)
  - Handle `audio` file upload
- [x] Write `QuestionUpdateView`: contributor can only edit their own questions — **ContributorRequiredMixin**
- [x] Wire up URLs: `/questions/`, `/questions/add/`, `/questions/<id>/edit/`
- [x] Write templates: list and form pages (include audio upload field and audio player if audio present)

**Check:** Admin can add global questions. Contributor can add and list their own questions. Contributor cannot edit another contributor's question. Teacher visiting `/questions/add/` gets 403.
- [x] Write templates for base.html and check for css js and templates files. 
---

## Stage 4 — `exams/` App

> **Değişiklik:** `students/` app kaldırıldı, bu nedenle ExamResult bağımlılığı yok. `TeacherQuestionIndex` bu app'e eklendi.
"Admin" adımı yoktu (hiçbir rol Django admin panelinden elle sınav oluşturmuyor). Yine de exams/admin.py debug/gözlem amaçlı eklendi — tek admin kullanıcı, kendi test sürecinde Exam ve TeacherQuestionIndex kayıtlarını incelemek için kullanacak, iş akışının zorunlu bir parçası değil.

### 4.1 Models
- [x] Create `exams` app
- [x] Write `Exam` model:
  - `teacher` FK (User)
  - `organization` FK (Organization)
  - `parameters` JSONField
  - `questions` M2M (Question)
  - `created_at`
- [x] Write `TeacherQuestionIndex` model:
  - `teacher` FK (User)
  - `question` FK (Question)
  - `used_at` DateTimeField (auto_now_add=True)
  - `Meta: unique_together = ('teacher', 'question')`
- [x] Create and apply migration

### 4.2 Service Layer (`services.py`)
> Write independently from views. Must be testable.

- [x] Create `ExamGeneratorService` class, accept `teacher` and `params` in constructor
- [x] `_calculate_counts()` → validate per-level exact counts sum to total (no percentage conversion — counts come in exact from the form)  

- [x] `_filter_questions()` → level + tag filter + `Q(org=None) | Q(org=teacher.org)` + exclude teacher's index
- [x] `_validate_counts()` →  raise meaningful error if not enough questions
- [x] `_sample_questions()` → draw randomly with `random.sample`, no duplicates
- [x] `_update_index()` → add selected question IDs to `TeacherQuestionIndex` for this teacher
- [x] `generate()` → orchestrate all above, create and return `Exam` instance

### 4.3 Form
- [x] Write `ExamGenerationForm`:
  - Total question count
  - Exact question count per level (6 inputs, one per CEFR level A1–C2)
  - JS live-validation: running sum of level counts must not exceed total; show remaining count as teacher types
  - Multi-select tags

### 4.4 Views
- [ ] Write `ExamCreateView`: call `ExamGeneratorService.generate()` if form is valid — **TeacherRequiredMixin**
- [ ] Write `ExamPreviewView`: display exam; show audio player/link if question has audio — **TeacherRequiredMixin**
- [ ] Write `ExamDownloadView`: generate and serve PDF; questions with audio get QR code or short URL in PDF — **TeacherRequiredMixin**
- [ ] Write `ExamHistoryView`: only own exams (`teacher=request.user`) — **TeacherRequiredMixin**
- [ ] Wire up URLs: `/exams/create/`, `/exams/<id>/preview/`, `/exams/<id>/download/`, `/exams/history/`

### 4.5 Templates
- [ ] `exams/create.html` — form page
- [ ] `exams/preview.html` — exam preview + download PDF button; audio player for listening questions
- [ ] `exams/history.html` — past exams list

**Check:** Create an exam, all questions visible in preview. Audio questions show a player. PDF downloads correctly. Error message shown when not enough questions. Another teacher's exam is inaccessible via URL. Same question does not appear in two different exams for the same teacher.

---

## Stage 5 — `dashboard/` App

- [ ] Create `dashboard` app (no models.py, no migrations)
- [ ] Write `DashboardHomeView`: last 5 exams + total exam count stat
- [ ] Write `ProfileView`: read-only user info
- [ ] Wire up URLs: `/dashboard/`, `/dashboard/profile/`
- [ ] Write `templates/dashboard/home.html`
- [ ] Write `templates/dashboard/profile.html`
- [ ] Add exam history and create exam links to `base.html` nav

**Check:** Recent exams visible on dashboard. Nav links work correctly.

---

## Stage 6 — `org/` App

> Org Admin panel. No models — reads from other apps.

- [ ] Create `org` app (no models.py, no migrations)
- [ ] Write `OrgDashboardView`: teacher count, question count, exam count for the org
- [ ] Write `TeacherListView`: all teachers in org
- [ ] Write `TeacherCreateView`: create User with `role=teacher`, same org as org_admin
- [ ] Write `TeacherDetailView`: teacher info + their generated exams
- [ ] Write `OrgQuestionListView`: all questions in org (read-only view)
- [ ] Write `OrgExamListView`: all exams in org
- [ ] Wire up URLs: `/org/`, `/org/teachers/`, `/org/questions/`, `/org/exams/`
- [ ] Write templates

**Check:** Org Admin can add a teacher. Org Admin can view all questions in their org (but not edit). Org Admin cannot access another org's data.

---

## Stage 7 — Polish & Deploy Prep

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
- [ ] Teacher cannot access `/questions/add/` or `/questions/<id>/edit/`?
- [ ] Teacher cannot access another teacher's exams via URL?
- [ ] Org Admin cannot access another org's data via URL?
- [ ] `is_active=False` questions never included in exam generation?
- [ ] `TeacherQuestionIndex` correctly prevents duplicate questions across exams?
- [ ] PDF export works and audio questions include a link/QR code?
- [ ] `python manage.py check --deploy` passes without warnings?

---

## Summary Table

| Stage | Content | Depends On |
|---|---|---|
| 0 | Project setup | — |
| 1 | `accounts/` | 0 |
| 2 | `core/` | 1 |
| 3 | `questions/` | 1, 2 |
| 4 | `exams/` | 1, 2, 3 |
| 5 | `dashboard/` | 1, 4 |
| 6 | `org/` | 1, 3, 4 |
| 7 | Polish & Deploy | 1–6 |

> **Removed:** Stage 4 (students/) entirely. Previous stages 5–8 renumbered to 4–7.

---

## NOTES
### DÜZENLENECEK
- [ ] **NOT:** `role` teacher, org_admin veya contributor olarak kaydedilince `user permissions` otomatik atansın — signal veya `save()` override ile yapılacak, mixin'ler tamamlandıktan sonra
- [ ] **NOT:** Audio dosyaları için storage backend production'da S3 veya benzeri bir şeye taşınabilir; şimdilik local `MEDIA_ROOT` yeterli
- [ ] **NOT:** PDF export için `reportlab` veya `weasyprint` seçimi yapılmalı — weasyprint HTML/CSS tabanlı olduğu için Bootstrap şablonlarıyla daha kolay entegre olur
