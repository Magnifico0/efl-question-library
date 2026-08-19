import random
from django.db.models import Q, Count
from questions.models import Question, Passage
from exams.models import Exam, TeacherQuestionIndex, ExamQuestion
from django.utils import timezone

class ExamGenerationError(Exception):
    """
    Raised when an exam cannot be generated with the given parameters,
    """
    pass


class ExamGeneratorService:
    """
    Encapsulates the exam generation algorithm. Independent from views
    so it can be tested and reused without touching request/response.
    """

    def __init__(self, teacher, params):
        self.teacher = teacher
        self.params = params
        self.level_counts = {}
        self.filtered_questions = {}
        self.filtered_passages = {}
        self.selected_questions = []
    
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

    def _filter_questions(self):
        self._load_used_ids()
        tag_ids = self.params.get("tags", [])

        base_qs = self._usable_questions_base_qs().filter(passage__isnull=True)

        for level, count in self.level_counts.items():
            qs = base_qs.filter(level=level)
            if tag_ids:
                qs = qs.filter(tags__id__in=tag_ids).distinct()
            self.filtered_questions[level] = list(qs)

    def _filter_passages(self):
        self.filtered_passages = {}
        section_configs = [
            ("reading", Passage.Kind.READING),
            ("listening", Passage.Kind.LISTENING)
        ]
        #!
        requested_levels = list(self.level_counts.keys())
        for prefix, kind in section_configs:
            passage_count = self.params.get(f"{prefix}_passage_count") or 0 
            if passage_count <=0:
                self.filtered_passages[prefix] = []
                continue
            questions_per_passage = self.params.get(f"{prefix}_questions_per_passage") or 0 
            min_required = questions_per_passage if questions_per_passage >0 else 1 

            usable_filter = (
                Q(questions__is_active=True) 
                & ~Q(questions__id__in=self.used_ids)
                & (Q(questions__organization=None) | Q(questions__organization=self.teacher.organization))
            )

            candidates = (
                Passage.objects.filter(kind=kind, level__in=requested_levels)
                .annotate(
                    active_question_count=Count(
                        "questions",
                        filter=usable_filter,
                    )
                )
                .filter(active_question_count__gte=min_required)
                .prefetch_related("questions")
            )

            self.filtered_passages[prefix] = list(candidates)
    def _validate_passage_availability(self,prefix,section_label,errors):
        passage_count = self.params.get(f"{prefix}_passage_count") or 0 
        if passage_count <=0:
            return
        candidates = self.filtered_passages.get(prefix,[])

        if len(candidates)<passage_count:
            errors.append(
                f"{section_label}: {passage_count} parça istendi, ama yeterli "
                f"soruya sahip sadece {len(candidates)} parça bulundu."
            )
            return
        questions_per_passage = self.params.get(f"{prefix}_questions_per_passage") or 0 
        if questions_per_passage > 0:
            return
        question_total = self.params.get(f"{prefix}_questions_total") or 0
        best_candidates = sorted(
            candidates, key=lambda p: p.active_question_count, reverse=True
        )[:passage_count]
        max_available = sum(p.active_question_count for p in best_candidates)

        if max_available <question_total:
            errors.append(
                f"{section_label} : {passage_count} parçadan topşaö {question_total} "
                f"soru istendi, ama seçilen parçardan en fazla {max_available} soru "
                f"sağlanabiliyor. Parça sayısını arttırın yada istenen soru sayısını azaltın"
            )

    def _passage_level_contribution(self):
        contribution = {}
        for prefix in ("reading","listening"):
            passage_count = self.params.get(f"{prefix}_passage_count") or 0 
            if passage_count <=0:
                continue
            candidates = self.filtered_passages.get(prefix,[])
            questions_per_passage = self.params.get(f"{prefix}_questions_per_passage") or 0 
            if questions_per_passage > 0:
                usable = [p for p in candidates if p.active_question_count >= questions_per_passage][:passage_count]
                for p in usable:
                    contribution[p.level] = contribution.get(p.level, 0) + questions_per_passage
            else:
                questions_total = self.params.get(f"{prefix}_questions_total") or 0
                best = sorted(candidates, key=lambda p: p.active_question_count, reverse=True)[:passage_count]
                allocation = self._distribute_evenly(best, questions_total)
                for p, cnt in allocation.items():
                    contribution[p.level] = contribution.get(p.level, 0) + cnt
        return contribution

    def _load_used_ids(self):
        self.used_ids = set(
            TeacherQuestionIndex.objects.filter(
                teacher = self.teacher
            ).values_list("question_id", flat=True)
        )

    def _usable_questions_base_qs(self):
        return Question.objects.filter(
            is_active = True,
        ).filter(
            Q(organization=None)| Q(organization = self.teacher.organization)
        ).exclude(id__in=self.used_ids)

    def _validate_counts(self):
        errors = []
        passage_contribution = self._passage_level_contribution()

        for level, count in self.level_counts.items():
            standalone_available = len(self.filtered_questions.get(level, []))
            available = standalone_available + passage_contribution.get(level, 0)
            if available < count:
                errors.append(
                    f"{level} seviyesinde {count} soru istendi, "
                    f"ama sadece {available} uygun soru bulundu."
                )

        self._validate_passage_availability("reading","Reading",errors)
        self._validate_passage_availability("listening","Listening",errors)

        if errors:
            raise ExamGenerationError(" ".join(errors))
    def _distribute_evenly(self,passages,total_questions):
        allocation = {p: 0 for p in passages}
        remaining = total_questions

        while remaining>0: 
            progressed = False
            for p in passages:
                if remaining <= 0: 
                    break
                if allocation[p] < p.active_question_count:
                    allocation[p] +=1
                    remaining -=1
                    progressed = True
            if not progressed:
                break
        return allocation

    def _select_passage_groups(self):
            
        """
        Reading/listening passage'larını seçer, her birinin alt sorularını belirler.
        Dönüş: [[q1, q2, q3], [q4, q5], ...] — her alt liste bir passage'ın soruları.
        """
        passage_groups = []

        section_configs = [
            ("reading", Passage.Kind.READING),
            ("listening", Passage.Kind.LISTENING),
        ]

        for prefix, kind in section_configs:
            passage_count = self.params.get(f"{prefix}_passage_count") or 0
            if passage_count <= 0:
                continue

            candidates = self.filtered_passages.get(prefix, [])
            selected_passages = random.sample(candidates, passage_count)
            questions_per_passage = self.params.get(f"{prefix}_questions_per_passage") or 0

            if questions_per_passage > 0:
                for passage in selected_passages:
                    active_questions = list(
                        self._usable_questions_base_qs().filter(passage=passage)
                    )
                    chosen = random.sample(active_questions, questions_per_passage)
                    passage_groups.append(chosen)
            else:
                questions_total = self.params.get(f"{prefix}_questions_total") or 0
                allocation = self._distribute_evenly(selected_passages, questions_total)
                for passage, count in allocation.items():
                    if count <= 0:
                        continue
                    active_questions = list(
                        self._usable_questions_base_qs().filter(passage=passage)
                    )
                    chosen = random.sample(active_questions, count)
                    passage_groups.append(chosen)

        return passage_groups


    def _select_standalone_questions(self, passage_groups):
        """Level bazlı standalone soruları seçer — passage'ların karşıladığı
        level miktarını düşerek."""
        passage_level_counts = {}
        for group in passage_groups:
            for q in group:
                passage_level_counts[q.level] = passage_level_counts.get(q.level, 0) + 1

        standalone_questions = []
        for level, count in self.level_counts.items():
            covered_by_passages = passage_level_counts.get(level, 0)
            remaining = count - covered_by_passages
            if remaining > 0:
                pool = self.filtered_questions.get(level, [])
                chosen = random.sample(pool, min(remaining, len(pool)))
                standalone_questions.extend(chosen)

        return standalone_questions


    def _build_ordered_list(self, standalone_questions, passage_groups):
        """Standalone soruları ve passage gruplarını, grup bütünlüğünü
        bozmadan (bir passage'ın soruları asla ayrılmadan) rastgele sıraya sokar."""
        blocks = [[q] for q in standalone_questions] + passage_groups
        random.shuffle(blocks)

        ordered = []
        for block in blocks:
            ordered.extend(block)
        return ordered


    def _sample_questions(self):
        """Sınav için soruları seçer ve sıraya koyar (self.ordered_questions)."""
        passage_groups = self._select_passage_groups()
        standalone_questions = self._select_standalone_questions(passage_groups)
        self.ordered_questions = self._build_ordered_list(standalone_questions, passage_groups)

    def _update_index(self):
        TeacherQuestionIndex.objects.bulk_create([
            TeacherQuestionIndex(teacher=self.teacher, question=q)
            for q in self.ordered_questions
        ])

    def generate(self):
        self._calculate_counts()
        self._filter_questions()
        self._filter_passages()
        self._validate_counts()
        self._sample_questions()

        exam_name = self.params.get("name") or timezone.now().strftime("%d-%m-%Y")
        exam = Exam.objects.create(
            teacher=self.teacher,
            organization=self.teacher.organization,
            name = exam_name,
            parameters=self.params,
        )
        ExamQuestion.objects.bulk_create([
            ExamQuestion(exam=exam, question=q,order=i)
            for i,q in enumerate(self.ordered_questions)
        ])
        self._update_index()
        return exam

    