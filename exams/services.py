import random
from django.db.models import Q
from questions.models import Question
from exams.models import Exam, TeacherQuestionIndex


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
        used_ids = TeacherQuestionIndex.objects.filter(
            teacher=self.teacher
        ).values_list("question_id", flat=True)

        tag_ids = self.params.get("tags", [])

        for level, count in self.level_counts.items():
            qs = Question.objects.filter(
                is_active=True,
                level=level,
            ).filter(
                Q(organization=None) | Q(organization=self.teacher.organization)
            ).exclude(id__in=used_ids)

            if tag_ids:
                qs = qs.filter(tags__id__in=tag_ids).distinct()

            self.filtered_questions[level] = list(qs)

    def _validate_counts(self):
        errors = []
        for level, count in self.level_counts.items():
            available = len(self.filtered_questions.get(level, []))
            if available < count:
                errors.append(
                    f"{level} seviyesinde {count} soru istendi, "
                    f"ama sadece {available} uygun soru bulundu."
                )
        if errors:
            raise ExamGenerationError(" ".join(errors))

    def _sample_questions(self):
        selected = []
        for level, count in self.level_counts.items():
            pool = self.filtered_questions[level]
            selected.extend(random.sample(pool, count))
        self.selected_questions = selected

    def _update_index(self):
        TeacherQuestionIndex.objects.bulk_create([
            TeacherQuestionIndex(teacher=self.teacher, question=q)
            for q in self.selected_questions
        ])

    def generate(self):
        self._calculate_counts()
        self._filter_questions()
        self._validate_counts()
        self._sample_questions()

        exam = Exam.objects.create(
            teacher=self.teacher,
            organization=self.teacher.organization,
            parameters=self.params,
        )
        exam.questions.set(self.selected_questions)

        self._update_index()

        return exam