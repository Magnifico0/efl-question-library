# Build Progress — English Question Bank System

> Check off each step as you complete it: `[ ]` → `[x]`
> Paste this file together with agent3.md at the start of every new chat.

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
              → Quick Wins / New Question Types / Passage / Rework / Scoring / Org Dashboard
                → Polish & Deploy (final stage)
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
  - `role` → `CharField(choices=[admin, org_admin, contributor, teacher])`
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `first_name` and `last_name` → override with `blank=False` (required)
- [x] Add `AUTH_USER_MODEL = 'accounts.User'` to `settings/base.py`
- [x] Create and apply migration — **must be done before any other migrations**

### 1.2 Admin
- [x] Write `OrganizationAdmin`
- [x] Write `UserAdmin`: `role`, `organization`, `first_name`, `last_name` visible

### 1.3 Auth Views
- [x] Write `LoginForm` (`forms.py`)
- [x] Write `login_view`: POST → role check → admin to `/admin/`, org_admin to `/org/`, contributor to `/questions/`, teacher to `/dashboard/`
- [x] Write `logout_view`
- [x] Write `role_redirect_view` (redirect already logged-in users to correct page)
- [x] Wire up URLs: `/login/`, `/logout/`

### 1.4 Mixins
- [x] Write `TeacherRequiredMixin`
- [x] Write `OrgAdminRequiredMixin`
- [x] Write `AdminRequiredMixin`
- [x] Write `ContributorRequiredMixin`

### 1.5 Template
- [x] Write `templates/accounts/login.html` (Bootstrap 5)

**Check:** Login as admin, org_admin, contributor, and teacher — each redirects to the correct page. Visiting `/dashboard/` without login redirects to `/login/`. ✅ Verified.

---

## Stage 2 — `core/` App

> Shared tools used by other apps. Write early so they're ready for later stages.

- [x] Create `core` app (no migrations folder — specify in `AppConfig`)
- [x] Write `OrgFilterMixin`: filter querysets by `request.user.organization`
- [x] Write `user_role_context` context processor: inject `role` into every template
- [x] Add context processor to `settings/base.py`
- [x] Create `core/templatetags/` folder
- [x] Write `active_nav` template tag: add Bootstrap `active` class to active nav link
- [x] Write `to_letter` template filter: converts 1→A, 2→B, ... for choice/answer-key lettering

**Check:** Writing `{{ role }}` in any template returns the correct value. ✅ Verified.

---

## Stage 3 — `questions/` App

### 3.1 Models
- [x] Create `questions` app
- [x] Write `TagCategory` model: `name`
- [x] Write `Tag` model: `name`, `category` FK
- [x] Write `Question` model:
  - `level` → `CharField(choices=[A1, A2, B1, B2, C1, C2])`
  - `text`, `image` (Pillow), `is_active`
  - `audio` → `FileField(upload_to='questions/audio/', null=True, blank=True)`
  - `audio_label` → `CharField(max_length=50, null=True, blank=True)` — e.g. "Part 1", print-only label
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

### 3.3 Contributor-Facing Views
> Contributors add questions; `organization` is never set from the contributor's own profile — contributor-created questions are always global (`organization=None`).

- [x] Write `QuestionForm`: `organization` and `created_by` fields **not in form**; `audio`, `audio_label` fields included
- [x] Write `ChoiceForm` and `ChoiceFormSet`: inline choice entry for contributor-facing question form
- [x] Write `QuestionListView`: only questions where `created_by=request.user` — **ContributorRequiredMixin**
- [x] Write `QuestionCreateView`:
  - Set `created_by` automatically in `form_valid()` (organization intentionally left unset)
  - Use `ContributorRequiredMixin`
  - Handle `ChoiceFormSet` inline (min 2 choices required)
  - Handle `audio` file upload + audio player in template
- [x] Write `QuestionUpdateView`: contributor can only edit their own questions — **ContributorRequiredMixin**
- [x] Wire up URLs: `/questions/`, `/questions/add/`, `/questions/<id>/edit/`
- [x] Write templates: list and form pages (audio upload field + `<audio controls>` player for existing audio)

**Check:** Admin can add global questions. Contributor can add and list their own questions. Contributor cannot edit another contributor's question. Teacher visiting `/questions/add/` gets redirected. ✅ Verified in browser.

---

## Stage 4 — `exams/` App

> `students/` app removed, no ExamResult dependency. `TeacherQuestionIndex` added here.
> `exams/admin.py` added for debug/observation purposes only (single admin user, not part of the required workflow).

### 4.1 Models
- [x] Create `exams` app
- [x] Write `Exam` model:
  - `teacher` FK (User) — `on_delete=CASCADE` (deleting the teacher deletes their exams, no orphaned records)
  - `organization` FK (Organization) — `on_delete=CASCADE` (deleting the org deletes its exams)
  - `parameters` JSONField
  - `questions` M2M (Question)
  - `created_at`
  - `Meta.ordering = ["-created_at"]`
- [x] Write `TeacherQuestionIndex` model:
  - `teacher` FK (User) — `on_delete=CASCADE`
  - `question` FK (Question) — `on_delete=CASCADE`
  - `used_at` DateTimeField (auto_now_add=True)
  - `Meta: unique_together = ('teacher', 'question')`
- [x] Create and apply migration

### 4.2 Service Layer (`services.py`)
- [x] Create `ExamGeneratorService` class, accept `teacher` and `params` in constructor
- [x] `_calculate_counts()` → validate per-level exact counts sum to `total` (no percentage conversion, counts come in exact from the form)
- [x] `_filter_questions()` → level + tag filter + `Q(org=None) | Q(org=teacher.org)` + exclude teacher's index
- [x] `_validate_counts()` → raise `ExamGenerationError` if not enough questions
- [x] `_sample_questions()` → draw randomly with `random.sample`, no duplicates
- [x] `_update_index()` → add selected question IDs to `TeacherQuestionIndex` for this teacher (bulk_create)
- [x] `generate()` → orchestrate all above, create and return `Exam` instance

### 4.3 Form
- [x] Write `ExamGenerationForm`:
  - Total question count
  - Exact question count per level (6 dynamically generated inputs, one per CEFR level A1–C2)
  - JS live-validation: running sum of level counts vs total, submit disabled until they match
  - Multi-select tags

### 4.4 Views
- [x] Write `ExamCreateView`: call `ExamGeneratorService.generate()` if form is valid — **TeacherRequiredMixin**
- [x] Write `ExamPreviewView`: display exam, choices, image/audio — **TeacherRequiredMixin**, ownership check via `get_object_or_404(teacher=request.user)`
- [x] Write `ExamDownloadView`: generate and serve PDF via weasyprint — **TeacherRequiredMixin**, ownership check
- [x] Write `ExamHistoryView`: only own exams (`teacher=request.user`) — **TeacherRequiredMixin**
- [x] Wire up URLs: `/exams/create/`, `/exams/<id>/preview/`, `/exams/<id>/download/`, `/exams/history/`

### 4.5 Templates
- [x] `exams/create.html` — form page + `static/css/exams.css` + `static/js/exam_create.js`
- [x] `exams/preview.html` — exam preview, choices lettered via `to_letter`, audio player
- [x] `exams/history.html` — past exams list
- [x] `exams/pdf.html` — standalone template (no `base.html` extend) for weasyprint, includes answer key page

**Check:** Create an exam, all questions visible in preview. Audio questions show a player. PDF downloads correctly with numbering, lettered choices, and an answer key. Error message shown when not enough questions. Another teacher's exam is inaccessible via URL (404). Same question does not appear in two different exams for the same teacher. ✅ Verified in browser.

---

## Stage 5 — `dashboard/` App

- [x] Create `dashboard` app (no models.py, no migrations)
- [x] Write `DashboardHomeView`: last 5 exams + total exam count stat
- [x] Write `ProfileView`: read-only user info
- [x] Wire up URLs: `/dashboard/`, `/dashboard/profile/`
- [x] Write `templates/dashboard/home.html`
- [x] Write `templates/dashboard/profile.html`
- [x] Add exam history and create exam links to `base.html` nav (role-conditional nav)

**Check:** Recent exams visible on dashboard. Nav links work correctly. ✅ Verified.

---

## Stage 6 — `org/` App

> Org Admin panel. No models — reads from other apps.

- [x] Create `org` app (no models.py, no migrations)
- [x] Write `OrgDashboardView`: teacher count, question count, exam count for the org
- [x] Write `TeacherListView`: all teachers in org
- [x] Write `TeacherCreateView`: create User with `role=teacher`, same org as org_admin
- [x] Write `TeacherDetailView`: teacher info + their generated exams
- [x] Write `OrgQuestionListView`: all questions accessible to org (global + org-scoped), read-only view
- [x] Write `OrgExamListView`: all exams in org
- [x] Wire up URLs: `/org/`, `/org/teachers/`, `/org/teachers/add/`, `/org/teachers/<id>/`, `/org/questions/`, `/org/exams/`
- [x] Write templates

**Check:** Org Admin can add a teacher. Org Admin can view all questions in their org (but not edit). Org Admin cannot access another org's data. ✅ Verified.

---

## Stage 8 — Quick Wins (Shuffle & PDF Header)

### 8.1 Şık Karıştırma
- [x] `ExamPreviewView` ve `ExamDownloadView` içinde, her soru için `choices.all()` bir kez çekilip `random.sample()` ile karıştırılsın — her açılışta (her GET isteğinde) yeniden karışacak şekilde, sabitlenmeyecek
- [x] `to_letter` filtresinin karışık sıraya göre doğru harfi verdiğini doğrula

### 8.2 PDF Header & Sınav Adı
- [x] `Exam` modeline `name` alanı ekle (`CharField(max_length=200, blank=True)`)
- [x] `ExamGenerationForm`'a sınav adı alanı ekle (opsiyonel, boş bırakılabilir)
- [x] `create.html`, `history.html`, `preview.html`'de sınav adını göster
- [x] `pdf.html` header'ını güncelle: ortada kurs adı (`exam.organization.name`), altında sınav adı (varsa), sağ üstte "Öğrenci Adı: ____", "Tarih: ____", "Puan: ____" için boş satırlar (elle doldurulacak, DB'ye kaydedilmeyecek — sistemde öğrenci kaydı yok)

**Check:** Aynı sınavı iki kez indirdiğinde şıkların farklı sırada geldiğini gör. PDF'te kurs ve sınav adı doğru görünüyor, öğrenci/tarih/puan satırları boş ve yazılabilir görünüyor.

---

## Stage 9 — Yeni Soru Tipleri

### 9.1 Fill in the Blank
- [x] `Question` modeline `correct_answer_text` alanı ekle (`CharField(max_length=500, null=True, blank=True)`)
- [x] `QuestionForms`'ta, tag "Fill in the Blank" seçiliyse `ChoiceFormSet` yerine bu alanın gösterilmesi (JS ile koşullu form değişimi — tag seçimine göre şık formseti gizlenip bu alan gösterilecek)
- [x] `pdf.html`/`preview.html`'de bu tip sorularda şık yerine boş alan/altı çizili satır render et

### 9.2 Eşleştirme (Matching)
- [x] `MatchingPair` modeli: `question` FK, `left_text`, `right_text`
- [x] Migration
- [x] `MatchingPairFormSet` (ChoiceFormSet'e benzer inline formset)
- [x] Contributor formunda, tag "Matching" seçiliyse bu formset gösterilsin
- [x] `pdf.html`'de iki sütunlu render: sol sütun numaralı, sağ sütun karışık harfli (şık karıştırma mantığı burada da uygulanır)

**Check:** Fill in the Blank sorusu şıksız kaydedilebiliyor. Matching sorusu çift olarak kaydedilip PDF'te iki sütun halinde, sağ taraf karışık sırayla görünüyor.

---

## Stage 10 — Passage Modeli (Bağımlı Soru Grupları)

> Reading (paragraf) ve Listening (ses) sorularının birden fazla alt soruyu paylaştığı yapı. Paragrafın kendi seviyesi vardır (A1-C2), tüm alt sorular bu seviyeyi miras alır — ayrı bir havuz olarak sayılmaz, mevcut seviye sayımına (`level_counts`) dahil olur.

### 10.1 Model
- [ ] `Passage` modeli:
  - `type` (`reading` / `listening`)
  - `level` (A1-C2, `Question.Level` ile aynı choices)
  - `text` (reading için, null=True)
  - `audio`, `audio_label` (listening için, null=True)
  - `created_by` FK
- [ ] `Question.passage` → yeni `ForeignKey(Passage, null=True, blank=True, related_name="questions")`
- [ ] `Question.level` alt sorularda artık elle girilmeyecek, `passage.level`'dan miras alınacak (view'da otomatik set edilir, formda gösterilmez)
- [ ] Migration

### 10.2 Contributor UI
- [ ] Soru listesinde/formunda "+ Paragraf/Ses Ekle" butonu
- [ ] Passage oluşturma formu (tip, seviye, metin veya ses yükleme)
- [ ] Passage'a bağlı olarak 3-5 alt soru eklenebilen bir akış (her alt soru kendi tag'iyle — MC/TF/Matching/Fill in the Blank olabilir — ama `passage` FK'si ve `level` ortak)
- [ ] `QuestionListView`'da passage'a bağlı sorular gruplu gösterilsin (paragraf başlığı altında alt sorular)

**Check:** Bir paragraf oluşturup altına 4 soru eklenebiliyor. Sorular listede paragrafla ilişkili ve doğru seviyede görünüyor.

---

## Stage 11 — Exam Generation Rework (Passage-Aware Sampling)

> En karmaşık aşama. Stage 10 tamamlanmadan başlanamaz.

### 11.1 Servis Katmanı Değişiklikleri
- [ ] `_filter_questions()`: bağımsız sorular ile passage'a bağlı sorular ayrı havuzlarda tutulsun, ama seviye sayımına (`level_counts`) birlikte dahil edilsin
- [ ] Yeni parametreler: `reading_passage_count`, `reading_questions_per_passage`, `listening_passage_count`, `listening_questions_per_passage`
- [ ] Passage seçimi: yeterli alt sorusu olan passage'lar arasından rastgele N passage seç
- [ ] Kısmi seçim: bir passage'ın 5 sorusu varsa, istenen sayı kadarını (örn. 3) o passage'dan seç (`random.sample` ile)
- [ ] `_validate_counts()`: passage sayısı/soru sayısı yeterliliğini de kontrol etsin, yetersizse anlamlı hata versin
- [ ] `_sample_questions()`: bağımsız soruları ve passage gruplarını birleştirirken, **her passage'ın soruları kendi içinde ardışık kalacak şekilde** sırala (gruplar kendi aralarında ve bağımsız sorularla karışabilir, ama bir grup başladıysa o grubun tüm soruları bitene kadar araya başka soru girmez)

### 11.2 Form Değişiklikleri
- [ ] `ExamGenerationForm`'a Reading/Listening için "kaç paragraf/ses, paragraf başına kaç soru" alanları eklensin
- [ ] JS doğrulaması: bu yeni alanlardan türeyen toplam soru sayısı da genel `total`'e dahil edilip canlı doğrulansın

**Check:** 2 paragraf, paragraf başına 3 soru istenirse, sınavda o 6 soru art arda ve doğru paragraflarla eşleşmiş halde geliyor. Yetersiz paragraf/soru varsa anlamlı hata veriyor.

---

## Stage 12 — Section Bazlı Puanlama

> Stage 10 ve 11 tamamlanmadan başlanamaz — "section" kavramı oradan geliyor.

- [ ] Sınav oluşturma formunda, her section tipi (Multiple Choice, True/False, Fill in the Blank, Matching, Reading, Listening) için puan girişi
- [ ] JS: (section soru sayısı × section puanı) toplamının 100'e eşit olduğunu canlı doğrula
- [ ] `Exam.parameters` JSON'una puanlama bilgisi eklensin (örn. `"scoring": {"reading": 5, "listening": 3, "fill_in_blank": 2}`)
- [ ] `pdf.html`'de her sorunun yanında puan değeri gösterilsin

**Check:** Farklı section'lara farklı puan verilip toplamın 100 olduğu, olmadığında hata verdiği doğrulanıyor.

---

## Stage 13 — Org Dashboard Zenginleştirme

> Düşük risk, kolay geri alınabilir — sadece görüntüleme katmanı, model/migration değişikliği gerektirmez.

- [ ] `OrgDashboardView`'a ek istatistikler: paragraf sayısı, listening parça sayısı, tip bazlı soru sayısı (MC / TF / Fill in the Blank / Matching / Reading / Listening), toplam havuz büyüklüğü
- [ ] `org/dashboard.html`'e bu yeni sayaçlar için ek kartlar

**Check:** Org admin panelinde detaylı soru havuzu dökümü doğru sayılarla görünüyor.

---

## Stage 14 — Polish & Deploy Prep

> Deploy hazırlıkları bilerek en sona bırakıldı — önce tüm yeni özellikler tamamlanacak, sonra deploy edilecek.

### General Templates
- [ ] `templates/404.html`, `templates/500.html`
- [ ] Add Django messages framework flash messages to base.html (already partially present — verify styling)

### Static Files
- [ ] Add WhiteNoise settings to `base.py`
- [ ] `python manage.py collectstatic` passes without errors

### Docker / Deploy
- [x] `Dockerfile` includes system dependencies for weasyprint (`libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf-2.0-0`, `libffi-dev`, `shared-mime-info`, `fonts-liberation`)
- [x] `entrypoint.sh` written: runs migrate, collectstatic, conditional non-interactive superuser creation, then starts gunicorn
- [ ] `settings/production.py`: parse `DATABASE_URL` from `os.environ` (no django-environ — manual parsing or a small dedicated parser)
- [ ] Set CSRF, SESSION, SECURE settings in `production.py`
- [ ] Configure Render (or chosen host): `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`
- [ ] Document `.env` variables

### Final Checks
- [ ] All views have login_required or a mixin?
- [ ] Teacher cannot access `/questions/add/` or `/questions/<id>/edit/`?
- [ ] Teacher cannot access another teacher's exams via URL?
- [ ] Org Admin cannot access another org's data via URL?
- [ ] `is_active=False` questions never included in exam generation?
- [ ] `TeacherQuestionIndex` correctly prevents duplicate questions across exams?
- [ ] PDF export works, choices/matching are shuffled, answer key and scoring are correct?
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
| 8 | Quick Wins (shuffle, PDF header) | 4 |
| 9 | Yeni soru tipleri (Fill in the Blank, Matching) | 3 |
| 10 | Passage modeli | 3, 9 |
| 11 | Exam generation rework | 4, 10 |
| 12 | Section bazlı puanlama | 11 |
| 13 | Org dashboard zenginleştirme | 6, 10 |
| 14 | Polish & Deploy | 1–13 |

---

## NOTES
### DÜZENLENECEK
- [ ] **NOT:** `role` teacher, org_admin veya contributor olarak kaydedilince `user permissions` otomatik atansın — signal veya `save()` override ile yapılacak, mixin'ler tamamlandıktan sonra
- [ ] **NOT:** Audio dosyaları için storage backend production'da S3 veya benzeri bir şeye taşınabilir; şimdilik local `MEDIA_ROOT` yeterli
- [x] **NOT:** PDF export için weasyprint seçildi — HTML/CSS tabanlı olduğu için Bootstrap şablonlarıyla entegrasyonu kolay oldu; Debian Trixie tabanlı imajlarda `libgdk-pixbuf2.0-0` yerine `libgdk-pixbuf-2.0-0` kullanılması gerekti.
- [ ] **NOT:** İleride bazı contributor'ların tüm soruları görmesi istenirse (sadece kendi eklediklerini değil), `User` modeline `can_view_all_questions` (BooleanField) eklenip `QuestionListView.get_queryset()` içinde dallandırılabilir. Kısıtlama tek bir yerde olduğu için bu küçük ve izole bir değişiklik olur.
- [ ] **NOT (Stage 11 öncesi netleştirilmeli):** Bir paragrafın soruları seviye sayımına (level_counts) dahil ediliyor — bu netleşti. Ama grup içi soru sırasının (paragraf içindeki 5 sorudan 3'ü seçildiğinde) kendi aralarında karışıp karışmayacağı netleşmedi, sadece "paragraflar arası ardışıklık" netleşti — bu detay Stage 11 tasarımı sırasında teyit edilecek.
