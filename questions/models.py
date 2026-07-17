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
    
class Question(models.Model):
    """
    level -> A1 to C2  --> textchoices
    question type -> text, image
    tags -> M2M tags 
    organization -> FK 
    created_by -> FK 
    """
    class Level(models.TextChoices):
        A1 = "A1","A1"
        A2 = "A2","A2"
        B1 = "B1","B1"
        B2 = "B2","B2"
        C1 = "C1","C1"
        C2 = "C2","C2"

    level = models.CharField(
        max_length=2,
        choices=Level.choices,
    )

    text = models.TextField()
    image  =models.ImageField(
        upload_to="questions/",
        null= True,
        blank=True,  
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
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="questions",
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
