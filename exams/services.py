import random

from django.db.models import Q
from django.utils import timezone

from questions.models import Question, Passage
from exams.models import Exam, TeacherQuestionIndex, ExamQuestion


# Tag filtresi passage sorularına da uygulansın mı?
# False  -> tag'ler sadece bağımsız (standalone) soruları daraltır. (mevcut davranış)
# True   -> passage soruları da tag filtresinden geçer (havuzu ciddi şekilde daraltır).
# Tek satırlık bilinçli bir karar olsun diye sabit hâlinde bırakıldı.
APPLY_TAGS_TO_PASSAGE_QUESTIONS = False


class ExamGenerationError(Exception):
    """Verilen parametrelerle sınav üretilemediğinde fırlatılır."""
    pass


class ExamGeneratorService:
    """
    Sınav üretim algoritması.

    TASARIM NOTU (Stage 11 revizyonu):
    Eskiden iki ayrı katman vardı: biri "bu parametrelerle üretmek mümkün mü?"
    diye TAHMİN ediyordu (_passage_level_contribution, _validate_passage_availability),
    diğeri gerçek seçimi yapıyordu (_select_passage_groups). Tahmin katmanı adayların
    ilk N tanesini varsayıyor, seçim katmanı random.sample ile başka N tanesini
    çekiyordu. İkisi farklı level dağılımı üretince kotalar kayıyor ve
    random.sample(pool, min(remaining, len(pool))) eksiği sessizce yutuyordu.

    Artık tahmin katmanı YOK. Seçim tek yetkili merci: bir slot doldurulamıyorsa
    tam o noktada ExamGenerationError fırlatılır. Böylece "doğrulama geçti ama
    sonuç eksik" durumu yapısal olarak imkânsız.
    """

    SECTION_CONFIGS = [
        ("reading", Passage.Kind.READING, "Reading"),
        ("listening", Passage.Kind.LISTENING, "Listening"),
    ]

    def __init__(self, teacher, params):
        self.teacher = teacher
        self.params = params
        self.level_counts = {}
        self.passage_slots = {}          # {"reading": [{"level": "B1", "question_count": 3}, ...]}
        self.passage_demand = {}         # {"B1": 5}  -> passage'lardan gelecek soru sayısı (level bazlı)
        self.independent_total = 0
        self.filtered_questions = {}
        self.filtered_passages = {}      # {("reading", "B1"): [Passage, ...]}
        self.used_ids = set()
        self.ordered_questions = []

    # ------------------------------------------------------------------ #
    # 1) Parametreleri oku ve aritmetiği kur
    # ------------------------------------------------------------------ #

    def _calculate_counts(self):
        total = self.params.get("total")
        levels = self.params.get("levels", {})

        if not total or total <= 0:
            raise ExamGenerationError("Toplam soru sayısı geçerli değil.")

        levels_sum = sum(levels.values())
        if levels_sum != total:
            raise ExamGenerationError(
                f"Seviyelere göre girilen soru sayıları toplamı ({levels_sum}) "
                f"toplam soru sayısına ({total}) eşit değil."
            )

        self.level_counts = levels
        self._read_passage_slots()
        self._compute_passage_demand()

    def _read_passage_slots(self):
        """params içindeki reading_passages / listening_passages listelerini okur."""
        for prefix, _kind, label in self.SECTION_CONFIGS:
            raw_slots = self.params.get(f"{prefix}_passages") or []
            slots = []
            for index, slot in enumerate(raw_slots, start=1):
                level = slot.get("level")
                count = slot.get("question_count") or 0
                if not level:
                    raise ExamGenerationError(
                        f"{label} parça #{index}: seviye seçilmemiş."
                    )
                if count <= 0:
                    raise ExamGenerationError(
                        f"{label} parça #{index}: soru sayısı 0'dan büyük olmalı."
                    )
                if level not in self.level_counts:
                    raise ExamGenerationError(
                        f"{label} parça #{index}: {level} seviyesi istendi, ama "
                        f"sınavın seviye dağılımında {level} için soru ayrılmamış."
                    )
                slots.append({"level": level, "question_count": count})
            self.passage_slots[prefix] = slots

    def _compute_passage_demand(self):
        """
        Passage'lardan gelecek soruların level bazlı toplamını çıkarır ve
        seviye kotalarını aşmadığını doğrular. Bağımsız soru hakkı buradan türer:
            independent_total = total - (tüm passage slotlarının toplamı)
        """
        demand = {}
        for prefix, _kind, _label in self.SECTION_CONFIGS:
            for slot in self.passage_slots.get(prefix, []):
                demand[slot["level"]] = demand.get(slot["level"], 0) + slot["question_count"]

        errors = []
        for level, needed in demand.items():
            quota = self.level_counts.get(level, 0)
            if needed > quota:
                errors.append(
                    f"{level} seviyesinde parçalardan {needed} soru istendi, ama bu "
                    f"seviye için ayrılan toplam soru sayısı {quota}."
                )
        if errors:
            raise ExamGenerationError(" ".join(errors))

        passage_total = sum(demand.values())
        total = self.params["total"]
        if passage_total > total:
            raise ExamGenerationError(
                f"Parçalardan gelen soru sayısı ({passage_total}), toplam soru "
                f"sayısını ({total}) aşamaz."
            )

        self.passage_demand = demand
        self.independent_total = total - passage_total

    # ------------------------------------------------------------------ #
    # 2) Havuzları hazırla
    # ------------------------------------------------------------------ #

    def _load_used_ids(self):
        self.used_ids = set(
            TeacherQuestionIndex.objects.filter(teacher=self.teacher)
            .values_list("question_id", flat=True)
        )

    def _usable_questions_base_qs(self):
        return (
            Question.objects.filter(is_active=True)
            .filter(Q(organization=None) | Q(organization=self.teacher.organization))
            .exclude(id__in=self.used_ids)
        )

    def _filter_questions(self):
        """Bağımsız (passage'sız) soru havuzları — level bazlı."""
        self._load_used_ids()
        tag_ids = self.params.get("tags", [])
        base_qs = self._usable_questions_base_qs().filter(passage__isnull=True)

        for level in self.level_counts:
            qs = base_qs.filter(level=level)
            if tag_ids:
                qs = qs.filter(tags__id__in=tag_ids).distinct()
            self.filtered_questions[level] = list(qs)

    def _passage_question_qs(self, passage):
        """Bir passage'ın kullanılabilir soruları — seçimde tek kaynak burasıdır."""
        qs = self._usable_questions_base_qs().filter(passage=passage)
        tag_ids = self.params.get("tags", [])
        if tag_ids and APPLY_TAGS_TO_PASSAGE_QUESTIONS:
            qs = qs.filter(tags__id__in=tag_ids).distinct()
        # Passage içi soru sırası korunmalı: yazıldığı sırayla (pk) getiriyoruz.
        return qs.order_by("pk")

    def _filter_passages(self):
        """
        Aday passage'ları (section, level) bazında toplar.

        DİKKAT: Burada artık annotate(Count(...)) ile "yaklaşık" bir sayı
        tutmuyoruz. Adayın kaç sorusu olduğunu, seçimde kullanılacak
        queryset'in TA KENDİSİ ile ölçüyoruz (_passage_question_qs).
        Sayım ile seçimin farklı kaynaklardan beslenmesi, eski bug'ın köküydü.
        """
        self.filtered_passages = {}

        for prefix, kind, _label in self.SECTION_CONFIGS:
            slots = self.passage_slots.get(prefix, [])
            if not slots:
                continue

            needed_levels = {slot["level"] for slot in slots}
            passages = Passage.objects.filter(kind=kind, level__in=needed_levels)

            for passage in passages:
                questions = list(self._passage_question_qs(passage))
                if not questions:
                    continue
                passage.usable_questions = questions
                key = (prefix, passage.level)
                self.filtered_passages.setdefault(key, []).append(passage)

    # ------------------------------------------------------------------ #
    # 3) Seçim — tek yetkili katman
    # ------------------------------------------------------------------ #

    def _select_passage_groups(self):
        """
        Her slot için bir passage seçer ve slotun istediği kadar soruyu çeker.

        Kurallar:
          * Aynı passage iki slotta kullanılamaz.
          * Büyük slotlar önce yerleşir (greedy) — küçük slotlar için elde daha
            çok seçenek kalır, aksi hâlde bol soruya sahip tek aday küçük bir
            slota harcanıp büyük slot açıkta kalabilir.
          * Doldurulamayan slot = anında hata. Sessiz eksilme yok.

        Dönüş: [[q1, q2, q3], [q4, q5], ...] — her alt liste bir passage'ın soruları.
        """
        passage_groups = []
        used_passage_ids = set()

        for prefix, _kind, label in self.SECTION_CONFIGS:
            slots = self.passage_slots.get(prefix, [])
            if not slots:
                continue

            # Slotları soru sayısına göre azalan sırada işle (greedy yerleştirme).
            ordered_slots = sorted(
                enumerate(slots, start=1),
                key=lambda item: item[1]["question_count"],
                reverse=True,
            )

            for slot_no, slot in ordered_slots:
                level = slot["level"]
                needed = slot["question_count"]

                candidates = [
                    p for p in self.filtered_passages.get((prefix, level), [])
                    if p.pk not in used_passage_ids
                    and len(p.usable_questions) >= needed
                ]

                if not candidates:
                    raise ExamGenerationError(
                        self._slot_error_message(prefix, label, slot_no, level, needed,
                                                 used_passage_ids)
                    )

                passage = random.choice(candidates)
                used_passage_ids.add(passage.pk)

                # Hangi sorular: rastgele seç, ama passage içindeki özgün
                # sırayı koru (pk'ya göre geri sırala).
                chosen = random.sample(passage.usable_questions, needed)
                chosen.sort(key=lambda q: q.pk)
                passage_groups.append(chosen)

        return passage_groups

    def _slot_error_message(self, prefix, label, slot_no, level, needed, used_passage_ids):
        """Öğretmene 'neden olmadı' sorusunun cevabını veren, aksiyon alınabilir mesaj."""
        all_at_level = self.filtered_passages.get((prefix, level), [])
        free = [p for p in all_at_level if p.pk not in used_passage_ids]
        big_enough = [p for p in free if len(p.usable_questions) >= needed]

        if not all_at_level:
            return (
                f"{label} parça #{slot_no}: {level} seviyesinde kullanılabilir "
                f"soruya sahip hiç parça bulunamadı."
            )
        if not free:
            return (
                f"{label} parça #{slot_no}: {level} seviyesinde {len(all_at_level)} parça "
                f"var, ama hepsi bu sınavda zaten kullanıldı. Aynı seviyeden daha az "
                f"parça isteyin."
            )
        if not big_enough:
            en_buyuk = max(len(p.usable_questions) for p in free)
            return (
                f"{label} parça #{slot_no}: {level} seviyesinden {needed} soruluk bir parça "
                f"istendi, ama kalan parçaların en fazla {en_buyuk} kullanılabilir sorusu var. "
                f"Bu parça için soru sayısını düşürün."
            )
        return f"{label} parça #{slot_no}: parça seçilemedi."

    def _select_standalone_questions(self, passage_groups):
        """
        Bağımsız soruları seçer.

        Passage'ların karşıladığı miktar self.passage_demand'den gelir — gerçek
        seçimden bağımsız DEĞİL, çünkü artık her slotun level'ı baştan kesin.
        Yine de savunma amaçlı, gerçekten seçilenle karşılaştırıp doğruluyoruz.
        """
        gercek = {}
        for group in passage_groups:
            for q in group:
                gercek[q.level] = gercek.get(q.level, 0) + 1

        if gercek != self.passage_demand:
            # Buraya düşmek bir programlama hatasıdır, kullanıcı hatası değil.
            raise ExamGenerationError(
                f"İç tutarlılık hatası: parçalardan beklenen dağılım "
                f"{self.passage_demand}, gerçekleşen {gercek}."
            )

        standalone = []
        errors = []
        for level, count in self.level_counts.items():
            remaining = count - self.passage_demand.get(level, 0)
            if remaining <= 0:
                continue
            pool = self.filtered_questions.get(level, [])
            if len(pool) < remaining:
                errors.append(
                    f"{level} seviyesinde {remaining} bağımsız soru gerekiyor, ama "
                    f"sadece {len(pool)} uygun soru bulundu."
                )
                continue
            standalone.extend(random.sample(pool, remaining))

        if errors:
            raise ExamGenerationError(" ".join(errors))

        return standalone

    def _build_ordered_list(self, standalone_questions, passage_groups):
        """
        Blokları karıştırır. Bir passage'ın soruları asla ayrılmaz ve kendi
        içindeki sırası korunur (_select_passage_groups pk'ya göre sıralıyor).
        """
        blocks = [[q] for q in standalone_questions] + passage_groups
        random.shuffle(blocks)

        ordered = []
        for block in blocks:
            ordered.extend(block)
        return ordered

    def _sample_questions(self):
        passage_groups = self._select_passage_groups()
        standalone_questions = self._select_standalone_questions(passage_groups)
        self.ordered_questions = self._build_ordered_list(standalone_questions, passage_groups)

        # Son kontrol: sözleşme gereği tam olarak `total` soru üretilmiş olmalı.
        total = self.params["total"]
        if len(self.ordered_questions) != total:
            raise ExamGenerationError(
                f"İç tutarlılık hatası: {total} soru istendi, "
                f"{len(self.ordered_questions)} soru üretildi."
            )

    # ------------------------------------------------------------------ #
    # 4) Kalıcılaştırma
    # ------------------------------------------------------------------ #

    def _update_index(self):
        TeacherQuestionIndex.objects.bulk_create([
            TeacherQuestionIndex(teacher=self.teacher, question=q)
            for q in self.ordered_questions
        ])

    def generate(self):
        self._calculate_counts()
        self._filter_questions()
        self._filter_passages()
        self._sample_questions()

        exam_name = self.params.get("name") or timezone.now().strftime("%d-%m-%Y")
        params_to_store = dict(self.params)
        params_to_store["independent_total"] = self.independent_total

        exam = Exam.objects.create(
            teacher=self.teacher,
            organization=self.teacher.organization,
            name=exam_name,
            parameters=params_to_store,
        )
        ExamQuestion.objects.bulk_create([
            ExamQuestion(exam=exam, question=q, order=i)
            for i, q in enumerate(self.ordered_questions)
        ])
        self._update_index()
        return exam