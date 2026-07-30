from django.db import models
from accounts.models import Organization, User
# Create your models here.
class TagCategory(models.Model):
    """
    grammer, skill, format etc
    """
    name= models.CharField(max_length=100)
    def __str__(self):
        return self.name
    class Meta: 
        verbose_name_plural  = "Tag Categories"

class Tag(models.Model):
    """
    name
    category -> FK 
    """
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Level(models.TextChoices):
    A1 = "A1","A1"
    A2 = "A2","A2"
    B1 = "B1","B1"
    B2 = "B2","B2"
    C1 = "C1","C1"
    C2 = "C2","C2" 
class Passage(models.Model):
    class Kind(models.TextChoices):
        READING = "reading","Reading"
        LISTENING = "listening","Listening"

    kind = models.CharField(
        max_length=20,
        choices=Kind.choices
    )
    level = models.CharField(
        max_length=2,
        choices=Level.choices
    )
    text = models.TextField(
        null=True,
        blank=True
    )
    audio = models.FileField(
        upload_to="passages/audio/",
        null=True,
        blank=True
    )
    audio_label = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    image = models.ImageField(
        upload_to="passages/images/",
        null=True,
        blank=True
    )
    image_label = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="passages"
    )
    def __str__(self):
        if self.text:
            preview = self.text[:30]
        elif self.audio_label:
            preview = self.audio_label 
        elif self.image_label:
            preview = self.image_label
        else : 
            preview="Unknown"
        return f"{self.get_kind_display()} - {self.level} - {preview}"

class Question(models.Model):
    """
    level -> A1 to C2  --> textchoices
    question type -> text, image
    tags -> M2M tags 
    organization -> FK 
    created_by -> FK 
    """


    class QuestionType(models.TextChoices):
        MC = "mc", "Multiple Choices"
        TF = "tf", "True - False"
        FIB = "fib", "Fill in the Blank"
        MATCHING = "matching", "Matching"
        OPEN_ENDED = "open_ended","Open Ended"

    class Section(models.TextChoices):
        GENERAL = "general", "General"
        READING = "reading","Reading"
        LISTENING = "listening","Listening"
        WRITING = "writing","Writing"
        SPEAKING = "speaking","Speaking"


    level = models.CharField(
        max_length=2,
        choices=Level.choices,
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default= QuestionType.MC,
    )
    section = models.CharField(
        max_length=20,
        choices=Section.choices,
        default=Section.GENERAL
    )
    word_count_instruction = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Örn: 150 kelime yazın - Sadece Open Ended Questions için"
    )


    text = models.TextField()
    image  =models.ImageField(
        upload_to="questions/images/",
        null= True,
        blank=True, 
        help_text="Örn: Part1 - Image 2 - sadece sınav çıktısında görünür. "

    )
    image_label = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    audio = models.FileField(
        upload_to="questions/audio/",
        null=True,
        blank=True,
    )
    audio_label = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Örn: Part1 - Track 2 - sadece sınav çıktısında görünür. "
    )
    correct_answer_text = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Fill in the Blank tipi için"
    )
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="questions",
    )
    passage = models.ForeignKey(
        Passage,
        on_delete=models.SET_NULL,
        null = True,
        blank= True,
        related_name="questions"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
    )

    def __str__(self):
        return f"{self.level} - {self.text[:30]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete= models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.question} - {self.text[:30]}"

class MatchingPair(models.Model):
    question= models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="matching_pairs"

    )
    left_text = models.CharField(
        max_length=255
    )
    right_text = models.CharField(
        max_length=255
    )
    def __str__(self):
        return f"{self.question}- {self.left_text} / {self.right_text}"

