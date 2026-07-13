from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

#organization has: name, slug, create_at ?
#slug for url 
class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class User(AbstractUser):
    #USER ROLE PART 
    class Role(models.TextChoices):  #user role 
        ADMIN = "admin", "Admin"
        ORG_ADMIN = "org_admin", "Organization Admin"
        TEACHER = "teacher", "Teacher"
        #for python = "written in db ", "display in admin and form"
    #USER CLASS 
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TEACHER,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    #abstract user -> first name, last name -> blank= true 
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
