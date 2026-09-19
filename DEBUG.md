# 🗺️ Debug Roadmap — efl-question-library

> Mentor notu: Bu plan senin gerçek koduna bakılarak hazırlandı, genel geçer tavsiye değil.
> Her gün bağımsızdır — bir günü yarım bırakıp ertesi gün devam edebilirsin, sıra bozulmaz.
> Her madde tek başına test edilebilir. Bir maddeyi bitirince kutucuğu işaretle, dopamin al, devam et.

---

## 📍 Şu An Buradayım

> Her oturumun başında/sonunda bu satırı güncelle — dosyayı yeniden okumadan kaldığın yeri bulursun.

**Gün:** Henüz başlamadım → Day 0
**Son yaptığım:** —
**Sıradaki adım:** `django-debug-toolbar` kurulumu (Day 0, ilk madde)

---

## ▶️ İlk 5 Dakika (buraya kadar okumana gerek yok, direkt başla)

Hiçbir şey düşünme, sadece şunu çalıştır — kurulum bitene kadar Day 0'ın geri kalanını okuma bile:

```bash
pip install django-debug-toolbar --break-system-packages
```

Çalıştı mı? Devam et, Day 0'ın 2. maddesine geç. Hata mı verdi? O hatayı çöz, sonra devam et — henüz hiçbir "gerçek" işe başlamadın, bu sadece alet çantasını açmak.

---

## 📊 Genel Bakış (tek bakışta)

| Gün | Konu | Risk Seviyesi | Tahmini Süre | Gerçek Süre |
|---|---|---|---|---|
| 0 | Ortam kurulumu | — | 2-3 saat | ___ |
| 1 | 🔒 Güvenlik & secrets | **Kritik** | 2-4 saat | ___ |
| 2 | 🔒 Yetkilendirme sınırları | **Yüksek** | 3-4 saat | ___ |
| 3 | 🐛 Exam generation bug'ları | **Yüksek** | 4-6 saat | ___ |
| 4 | ⚡ Performans (N+1) | Orta | 2-3 saat | ___ |
| 5 | 🧹 Kod kalitesi & doküman senkronu | Orta | 3-4 saat | ___ |
| 6+ | 🧪 Test altyapısı | Uzun vadeli | Sürekli | ___ |
| Bonus | Ek geliştirme fırsatları | Düşük-Orta | İstediğin zaman | ___ |

> 💡 "Gerçek Süre" sütununu doldur — ADHD'de zaman tahmini genelde sapar, bunu görmek gelecekteki tahminlerini düzeltmene yardım eder. Doğru/yanlış çıkması önemli değil, sadece yaz.

**Kural:** Bir günde tıkanırsan, o günü yarım bırak, bir sonrakine geç. Sırayı zorlama.

**⏱️ 30 dakika kuralı:** Bir alt-madde üzerinde 30 dakikadan fazla tıkanırsan dur. Ya bulduğunu ne olursa olsun not al ve geç, ya da "çözemedim" diye işaretleyip sıradaki maddeye atla. Aynı maddede 1 saatten fazla kalmak, ADHD'de "tek maddeye kilitlenip günün geri kalanını kaybetme" tuzağıdır — bilerek engelliyoruz.

**🅿️ Parking Lot (Bekleme Alanı):** Bir gün üzerinde çalışırken aklına başka bir gün/madde ile ilgili bir fikir gelirse, **oraya gitme** — aşağıya, dosyanın en altındaki Parking Lot bölümüne tek satır not düş, kaldığın yere devam et. Odağı bölme, sadece fikri kaybetme.

---

## 🧰 Day 0 — Ortam Kurulumu

**Bugün SADECE bunu yap:** Kanıt toplama araçlarını kur, hiçbir şeyi düzeltme.

- [ ] `django-debug-toolbar` kur (sadece `local.py`'de, production'da değil)
  ```bash
  pip install django-debug-toolbar --break-system-packages
  ```
- [ ] `INSTALLED_APPS` ve `MIDDLEWARE`'e ekle
- [ ] Django shell'i aç, dene:
  ```bash
  docker compose exec web uv run python manage.py shell
  ```
- [ ] Shell içinde şunu çalıştırıp anla:
  ```python
  from django.db import connection, reset_queries
  reset_queries()
  # herhangi bir queryset çalıştır
  print(len(connection.queries))
  ```

✅ **Bitti sayılır:** Debug toolbar bir sayfada görünüyor, SQL panel açılıyor.

---

## 🔒 Day 1 — Güvenlik & Secrets Hijyeni

**Bugün SADECE bunu yap:** `.env` sızıntısını kapat, `ALLOWED_HOSTS`'u düzelt.

### 1.0 — Güvenlik ağı (Day 1'e başlamadan önce, 5 dakika)
- [ ] `git checkout -b debug-roadmap-yedek` ile bir yedek branch aç
- [ ] Bugün git geçmişiyle oynayacaksın (`git rm --cached`, belki `filter-repo`) — bir şey ters giderse geri dönebileceğin bir nokta olsun

### 1.1 — `.env` public repo'da (doğrulandı ✅)
- [ ] `git rm --cached .env` çalıştır, commit at
- [ ] `SECRET_KEY`'i rotate et (yeni rastgele değer üret)
- [ ] DB şifresini rotate et
- [ ] Gerçek bir `.env.example` oluştur (placeholder değerlerle) — şu an bu dosya **yok** (404 döndü)
- [ ] `git log --all --full-history -- .env` çalıştırıp geçmişte kaç kez göründüğünü gör

> 💡 Neden önemli: `.gitignore`'a eklemek geçmiş commit'leri silmez. Klasik hata.

### 1.2 — `ALLOWED_HOSTS = ['*']`
- [ ] `config/settings/production.py`'de bul
- [ ] Gerçek domain(ler)inle değiştir: `ALLOWED_HOSTS = ['seninsiten.com']`
- [ ] Şunu çalıştır ve **her satırını oku**:
  ```bash
  docker compose exec web uv run python manage.py check --deploy
  ```
- [ ] Çıkan her uyarı için: ne demek, neden önemli — bir not defterine yaz

✅ **Bitti sayılır:** `.env` git'ten çıktı, secrets rotate edildi, `check --deploy` çıktısı elinde.

---

## 🔒 Day 2 — Yetkilendirme Sınırları (IDOR Taraması)

**Bugün SADECE bunu yap:** "Başka birinin verisine erişebilir miyim?" sorusunu her view için sor.

### 2.1 — Rol kontrolü tekrarı
- [ ] `accounts/mixins.py` aç, 4 mixin'e bak (`TeacherRequiredMixin` vb.)
- [ ] Hepsinin `request.user.role != "teacher"` gibi **ham string** kullandığını gör
- [ ] `User.Role.TEACHER` enum'unun var olduğunu ama kullanılmadığını doğrula
- [ ] Not al: bu neden kırılgan? (typo riski, IDE desteği yok)

### 2.2 — Her view için scope kontrolü
Şu tabloyu kendin doldur — her view'ın `get_object`/`get_queryset`'ine bak:

| View | Doğru scope var mı? |
|---|---|
| `ExamPreviewView` | [ ] kontrol et |
| `ExamDownloadView` | [ ] kontrol et |
| `QuestionUpdateView` | [ ] kontrol et |
| `PassageDetailView` | [ ] kontrol et |
| `TeacherDetailView` | [ ] kontrol et |
| `QuestionCreateView.get_passage()` | [ ] kontrol et |

### 2.3 — Ölü kod: `OrgFilterMixin` (doğrulandı ✅)
- [ ] `grep -rn "OrgFilterMixin" .` çalıştır
- [ ] `core/mixins.py`'de tanımlı ama `org/views.py`'de **hiç kullanılmadığını** gör
- [ ] `agent4.md`'de "Stage 2 done" yazdığını ama gerçekte devrede olmadığını karşılaştır

> 💡 Neden önemli: biri ileride "zaten var" deyip bu mixin'i kullanırsa, davranış mevcut kodla **farklı** olur (global soruları filtreleme mantığı eksik).

### 2.4 — Kozmetik mi, gerçek bug mu? (typo karşılaştırması)
- [ ] `questions/urls.py`'de `path("pasages/<int:pk>/", ...)` satırını bul (eksik "s")
- [ ] `grep -rn "passage_detail" .` çalıştır — her yerde `reverse()`/`{% url %}` ile mi çağrılıyor?
- [ ] Sonucuna karar ver: bu bir bug mu değil mi? Neden?

### 2.5 — Yanıltıcı arayüz metni + ölü hidden alan (yeni bulgu ✅)
- [ ] `question_form.html`'de şu satırı bul: *"Seviye ... paragraftan otomatik alınıyor, **değiştirilemez**."*
- [ ] Bu metin `get_from_kwargs` typo'su yüzünden **yalan söylüyor** — alan gerçekte disabled değil, kullanıcı değiştirebiliyor gibi görünüyor (arka planda `form_valid()` sessizce eziyor). Bunu 2.3'teki bulgunla birleştirip anla: aynı bug'ın hem kod hem UX yansıması.
- [ ] Aynı template'te `<input type="hidden" name="passage" value="...">` satırını bul — `QuestionForms.Meta.fields`'de `"passage"` var mı kontrol et (yok). Bu input'un hiç okunmadığını, tamamen ölü olduğunu doğrula.

✅ **Bitti sayılır:** Tabloyu doldurdun, 3 "sessiz sapma" bulgusunun (2.3, 2.4, 2.5) hangisinin gerçek risk taşıdığını, hangisinin kozmetik olduğunu birkaç cümleyle açıklayabiliyorsun.

---

## 🐛 Day 3 — Exam Generation Bug'ları (en karmaşık gün, zamanı böl)

**Bugün SADECE bunu yap:** İki bilinen bug'ı kendi ortamında tetikleyip kanıtla.

### 3.1 — Çift rastgele çekiliş tutarsızlığı
- [ ] `exams/services.py` → `_validate_passage_availability()` oku
- [ ] `exams/services.py` → `_select_passage_groups()` oku
- [ ] Farkı bul: biri "en iyi kapasiteli" passage'ları mı seçiyor, biri "rastgele" mi?
- [ ] Shell'de test verisi oluştur: kapasitesi dengesiz 3-4 passage (biri 5 soru, biri 1 soru)
- [ ] `generate()`'i 10-15 kez art arda çağır, her seferinde dönen soru sayısını yazdır
- [ ] İstenenden az soru dönen bir çalıştırma yakala

### 3.2 — `passage.level` vs `question.level` varsayımı
- [ ] `questions/mixins.py` → `QuestionSaveMixin.form_valid()` oku
- [ ] `question.level = passage.level` satırını bul — bu enforcement'ın **nerede** çalıştığını anla
- [ ] Django admin'den bir soruyu aç, level'ını bağlı olduğu passage'dan **farklı** yap, kaydet
- [ ] O soruyu içeren bir sınav üretmeyi dene — ne oluyor, gözlemle ve not al

✅ **Bitti sayılır:** İki bug'ı da kendi ortamında en az bir kez tetikledin, ne olduğunu yazılı olarak açıklayabiliyorsun (henüz düzeltme).

---

## ⚡ Day 4 — Performans (N+1 Avı)

**Bugün SADECE bunu yap:** Debug toolbar açıkken sayfa gez, sorgu sayısı say.

- [ ] `/exams/create/` → POST sonrası SQL panelini kontrol et
- [ ] Passage sayısını artırıp azalt — sorgu sayısı **orantılı** artıyor mu? (N+1 belirtisi)
- [ ] `/exams/<id>/preview/` → aynı kontrolü yap
- [ ] `/questions/` → `grouped_questions` oluşturma mantığını kontrol et
- [ ] `_select_passage_groups()`'ta `prefetch_related("questions")` gerçekten kullanılıyor mu, yoksa boşa mı gidiyor? Kanıtla (tahmin etme)

✅ **Bitti sayılır:** Her sayfa için "kaç sorgu" rakamını not aldın, en az bir N+1 örneği bulup bulmadığına karar verdin.

---

## 🧹 Day 5 — Kod Kalitesi & Doküman Senkronu

**Bugün SADECE bunu yap:** `progress4.md`'deki `[x]` işaretlerini koddan tek tek doğrula.

- [ ] Stage 11.1, 11.2, 11.3 maddelerini aç
- [ ] Her maddeyi gerçek kodda ara, gerçekten yapılmış mı kontrol et
- [ ] Sapma bulduğun her maddeye not düş (dosyanın kendisine, gelecekteki AI oturumları için)
- [ ] 4 tekrarlı `*RequiredMixin` sınıfını fark et — **bu hafta dokunma**, sadece not al

✅ **Bitti sayılır:** Doküman/kod sapma listesi elinde. Henüz refactor yok.

---

## 🧪 Day 6+ — Test Altyapısı (sürekli)

**Kural:** Her bug için önce **başarısız test yaz**, sonra düzelt.

- [ ] `pytest-django` veya Django'nun kendi `TestCase`'i kur
- [ ] Day 3'teki 2 bug için önce reprodüksiyon testi yaz (kırmızı)
- [ ] Sonra düzelt (yeşil)
- [ ] IDOR kontrolleri için (Day 2) her rol için "başka birinin verisine erişemez" testi yaz

---

## 🎁 Bonus — Ek Geliştirme Fırsatları

Sohbet sırasında detaylandırmadığım ama gördüğüm ek noktalar:

- [ ] **`on_delete` tutarsızlığı:** `User.organization` → `SET_NULL`, ama `Exam.organization` ve `Question.organization` → `CASCADE`. Bir org silinirse kullanıcı kalır ama tüm sınavları/soruları silinir. Bilinçli bir karar mı, kaza mı?
- [ ] **Model-level validation eksik:** `Passage.level`/`Question.level` eşitliği, MC sorularda en az 2 seçenek, en az 1 doğru cevap — hepsi sadece **form/view katmanında** zorlanıyor. Django admin'den veya shell'den bypass edilebilir. `full_clean()` + model `clean()` metodları eklemeyi düşün (zaten `agent4.md`'nin CSV import notunda bu yaklaşım planlanmış).
- [ ] **`ExamQuestion.order` unique değil:** `unique_together = ("exam","question")` var ama `(exam, order)` yok — teorik olarak aynı sınavda iki soru aynı `order`'a sahip olabilir.
- [ ] **Pagination yok:** `QuestionListView`, `ExamHistoryView`, `OrgQuestionListView` gibi liste view'ları büyük veri setinde yavaşlayacak — `paginate_by` ekle.
- [ ] **`LOGGING` config yok:** `settings/base.py`'de hiç logging tanımı yok — production'da hata görünürlüğü sıfır. Sentry veya en azından dosya bazlı logging ekle.
- [ ] **Login'de brute-force koruması yok:** `django-axes` veya benzeri bir rate-limit paketi düşün (şu an düşük öncelik, küçük okul sistemi için).
- [ ] **`Exam.parameters` JSONField şemasız:** Zamanla (Stage 11 REVISED gibi) format değişebiliyor ama eski kayıtlar eski formatta kalıyor — geriye dönük okurken format kontrolü var mı, düşün.
- [ ] **Template'lerde XSS/CSRF taraması yapıldı, temiz çıktı** ✅ — `|safe`, `autoescape off`, `mark_safe` hiçbir yerde yok, CSRF token'lar doğru yerlerde. Bunu tekrar taramana gerek yok, sadece bilgin olsun.

---

## 📓 Bulgu Günlüğü (her gün için doldur)

Her gün bittiğinde şu 4 soruyu kısaca cevapla — uzun yazma, madde madde yeter:

```
Gün: ___
Ne buldum:
Nasıl doğruladım (komut/adım):
Şaşırtıcı mıydı, beklediğim gibi miydi:
Yarın ilk bakacağım şey:
```

---

## 🅿️ Parking Lot

Odaklandığın günün dışında aklına gelen fikirleri buraya tek satır at, geri dönme:

- 
- 
- 

---

## 📝 Nasıl İlerleyeceğim?

1. Her gün bittiğinde bulduklarını not al (doğru/yanlış fark etmez)
2. Takıldığın yerde günü yarım bırak, sonrakine geç
3. Bir bug'ı düzeltmeden önce mutlaka **kanıtla** (shell'de tetikle, debug toolbar'da göster)
4. Düzeltirken önce test yaz, sonra kodu değiştir

**Bu dosyayı projenin köküne koy, ilerledikçe kutucukları işaretle — hem ilerlemeni görürsün hem de gelecekteki sen (ya da bir AI oturumu) nerede kaldığını anlar.**
