# Build Progress — English Question Bank System

> Her adımı bitirince `[ ]` → `[x]` yap.
> Bir sonraki chat'e bu dosyayı da agent.md ile birlikte yapıştır.

---

## Neden Bu Sıra?

```
Proje kurulumu
  → accounts/   (her şey User'a bağlı, önce o olmalı)
    → core/     (mixin'ler accounts'a bağlı)
      → questions/  (soru bankası, User + Org gerektirir)
        → exams/    (questions ve accounts gerektirir)
          → dashboard/  (exams'i okur, en son gelir)
            → Polish    (template, static, deploy)
```

---

## Aşama 0 — Proje Kurulumu

- [ ] `uv` ile yeni proje oluştur, `requirements` dosyasını hazırla
- [ ] `django-admin startproject config .` — proje adı `config`
- [ ] `settings/` klasörünü oluştur: `base.py`, `local.py`, `production.py`
- [ ] `base.py`'a temel ayarları taşı (INSTALLED_APPS, TEMPLATES, STATIC, MEDIA)
- [ ] `local.py`: DEBUG=True, local PostgreSQL bağlantısı
- [ ] `production.py`: DEBUG=False, SECRET_KEY env'den, ALLOWED_HOSTS
- [ ] `docker-compose.yml` yaz: `web` + `db` servisleri
- [ ] `Dockerfile` yaz
- [ ] `.env.example` dosyası oluştur
- [ ] `python manage.py check` hatasız geçsin

**Kontrol:** `docker compose up` ile proje ayağa kalksın, Django karşılama sayfası görünsün.

---

## Aşama 1 — `accounts/` Uygulaması

> Diğer tüm app'ler User ve Organization'a bağlı. Bu app olmadan hiçbir şey yazılamaz.

### 1.1 Modeller
- [ ] `accounts` app'ini oluştur, `INSTALLED_APPS`'e ekle
- [ ] `Organization` modelini yaz: `name`, `slug`, `created_at`
- [ ] `User` modelini yaz (AbstractUser):
  - `role` → `CharField(choices=[admin, teacher])`
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `first_name` ve `last_name` → `blank=False` olarak override et (zorunlu)
- [ ] `settings/base.py`'a `AUTH_USER_MODEL = 'accounts.User'` ekle
- [ ] Migration oluştur ve uygula — **başka migration olmadan önce bu yapılmalı**

### 1.2 Admin
- [ ] `OrganizationAdmin` yaz
- [ ] `UserAdmin` yaz: `role`, `organization`, `first_name`, `last_name` görünsün

### 1.3 Auth Views
- [ ] `LoginForm` yaz (`forms.py`)
- [ ] `login_view` yaz: POST → rol kontrolü → admin `/admin/`'e, teacher `/dashboard/`'a
- [ ] `logout_view` yaz
- [ ] `role_redirect_view` yaz (giriş yapılmışsa doğru yere yönlendir)
- [ ] URL'leri bağla: `/login/`, `/logout/`

### 1.4 Mixin'ler
- [ ] `TeacherRequiredMixin` yaz
- [ ] `AdminRequiredMixin` yaz

### 1.5 Template
- [ ] `templates/accounts/login.html` yaz (Bootstrap 5)

**Kontrol:** Admin ve teacher ile giriş yap, doğru sayfalara yönlendirilsin. Giriş yapılmadan `/dashboard/`'a gitmeye çalışınca `/login/`'e dönsün.

---

## Aşama 2 — `core/` Uygulaması

> Diğer app'lerde kullanılacak ortak araçlar. Erken yazılırsa sonraki adımlarda hazır olur.

- [ ] `core` app'ini oluştur (migrations klasörü olmayacak — `AppConfig`'de belirt)
- [ ] `OrgFilterMixin` yaz: queryset'i `request.user.organization`'a göre filtrele
- [ ] `user_role_context` context processor yaz: her template'e `role` inject et
- [ ] `settings/base.py`'a context processor'ı ekle
- [ ] `core/templatetags/` klasörünü oluştur
- [ ] `active_nav` template tag'ini yaz: aktif nav linkine Bootstrap `active` class'ı ekle

**Kontrol:** Herhangi bir template'de `{{ role }}` yazınca doğru değeri dönsün.

---

## Aşama 3 — `questions/` Uygulaması

### 3.1 Modeller
- [ ] `questions` app'ini oluştur
- [ ] `TagCategory` modelini yaz: `name`
- [ ] `Tag` modelini yaz: `name`, `category` FK
- [ ] `Question` modelini yaz:
  - `level` → `CharField(choices=[A1, A2, B1, B2, C1, C2])`
  - `text`, `image` (Pillow), `is_active`
  - `tags` → M2M (Tag)
  - `organization` → `ForeignKey(Organization, null=True, blank=True)`
  - `created_by` → `ForeignKey(User, null=True, blank=True)`
- [ ] `Choice` modelini yaz: `question` FK, `text`, `is_correct`
- [ ] Migration oluştur ve uygula

### 3.2 Admin (Global Sorular)
- [ ] `ChoiceInline` yaz (Question admin içinde satır satır seçenek girişi)
- [ ] `QuestionAdmin` yaz: level / tag / is_active / organization filtreleri
- [ ] `TagAdmin` ve `TagCategoryAdmin` yaz
- [ ] Birkaç örnek soru admin'den ekle (test için)

### 3.3 Teacher-Facing Views (Org'a Özel Sorular)
- [ ] `QuestionForm` yaz: `organization` ve `created_by` alanları **form'da yok**
- [ ] `QuestionListView` yaz: sadece `created_by=request.user` olan sorular
- [ ] `QuestionCreateView` yaz:
  - `form_valid()` içinde `organization` ve `created_by` otomatik set et
  - `TeacherRequiredMixin` kullan
- [ ] `QuestionUpdateView` yaz: sadece kendi sorusunu düzenleyebilsin
- [ ] URL'leri bağla: `/questions/`, `/questions/add/`, `/questions/<id>/edit/`
- [ ] Template'leri yaz: liste ve form sayfaları

**Kontrol:** Admin global soru ekleyebilsin. Teacher kendi sorusunu ekleyip listeleyebilsin, başkasının sorusunu düzenleyemesin.

---

## Aşama 4 — `exams/` Uygulaması

### 4.1 Model
- [ ] `exams` app'ini oluştur
- [ ] `Exam` modelini yaz:
  - `teacher` FK (User)
  - `organization` FK (Organization)
  - `parameters` JSONField
  - `questions` M2M (Question)
  - `created_at`
- [ ] Migration oluştur ve uygula

### 4.2 Servis Katmanı (`services.py`)
> View'dan bağımsız yaz. Test edilebilir olsun.

- [ ] `ExamGeneratorService` class'ını oluştur, constructor'a `teacher` ve `params` al
- [ ] `_calculate_counts()` → yüzde aralıklarını tam sayıya çevir
- [ ] `_filter_questions()` → seviye + tag filtresi + `Q(org=None) | Q(org=teacher.org)`
- [ ] `_validate_counts()` → yetersiz soru varsa anlamlı hata fırlat
- [ ] `_sample_questions()` → `random.sample` ile rastgele çek, tekrar yok
- [ ] `generate()` → hepsini orkestre et, `Exam` oluştur ve döndür

### 4.3 Form
- [ ] `ExamGenerationForm` yaz:
  - Toplam soru sayısı
  - Her seviye için min/max yüzde alanları
  - Tag çoklu seçim

### 4.4 Views
- [ ] `ExamCreateView` yaz: form geçerliyse `ExamGeneratorService.generate()` çağır
- [ ] `ExamPreviewView` yaz: sınavı göster, yazdır butonu
- [ ] `ExamHistoryView` yaz: `OrgFilterMixin` ile sadece kendi org sınavları
- [ ] URL'leri bağla

### 4.5 Template'ler
- [ ] `exams/create.html` — form sayfası
- [ ] `exams/preview.html` — sınav önizleme + yazdır butonu
- [ ] `exams/history.html` — geçmiş sınavlar listesi

**Kontrol:** Sınav oluştur, preview'da tüm sorular görünsün. Yetersiz soru durumunda hata mesajı çıksın. Başka org sınavı URL'den erişilemesin.

---

## Aşama 5 — `dashboard/` Uygulaması

- [ ] `dashboard` app'ini oluştur (models.py yok, migration yok)
- [ ] `DashboardHomeView` yaz: son 5 sınav + toplam sınav sayısı istatistiği
- [ ] `ProfileView` yaz: kullanıcı bilgileri read-only
- [ ] URL'leri bağla: `/dashboard/`, `/dashboard/profile/`
- [ ] `templates/dashboard/home.html` yaz
- [ ] `templates/dashboard/profile.html` yaz
- [ ] `base.html` nav'ına soru bankası ve sınav oluştur linklerini ekle

**Kontrol:** Dashboard'da son sınavlar görünsün. Nav linkleri doğru çalışsın.

---

## Aşama 6 — Polish & Deploy Hazırlığı

### Genel Template
- [ ] `templates/base.html` — Bootstrap 5 navbar, footer, block yapısı
- [ ] `templates/404.html`, `templates/500.html`
- [ ] Flash mesajları (Django messages framework) base.html'e ekle

### Statik Dosyalar
- [ ] WhiteNoise ayarlarını `base.py`'a ekle
- [ ] `python manage.py collectstatic` hatasız geçsin

### Güvenlik & Production
- [ ] `production.py`'da CSRF, SESSION, SECURE ayarlarını yap
- [ ] `nginx.conf` yaz
- [ ] `docker-compose.prod.yml` yaz
- [ ] `.env` değişkenlerini dokümante et

### Son Kontroller
- [ ] Tüm view'larda login_required veya mixin var mı?
- [ ] Teacher başka org'un sınavına / sorusuna URL'den erişemiyor mu?
- [ ] `is_active=False` sorular sınava girmiyor mu?
- [ ] `python manage.py check --deploy` uyarısız geçsin

---

## Özet Tablo

| Aşama | İçerik | Bağımlılık |
|---|---|---|
| 0 | Proje kurulumu | — |
| 1 | `accounts/` | 0 |
| 2 | `core/` | 1 |
| 3 | `questions/` | 1, 2 |
| 4 | `exams/` | 1, 2, 3 |
| 5 | `dashboard/` | 1, 4 |
| 6 | Polish & Deploy | 1–5 |