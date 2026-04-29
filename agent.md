# Project Context: English Question Bank System

## What This Is
A Django web application for English language schools. Teachers log in and generate automatic exams from a question bank. No public API, no mobile app — web only.

## Tech Stack
- Python 3.12+, Django 5.x, PostgreSQL
- uv (package manager), Docker + Docker Compose
- Bootstrap 5, django-crispy-forms + crispy-bootstrap5
- Pillow, whitenoise, gunicorn, nginx
- Environment variables via os.environ (no django-environ)

## Two User Roles
**Admin** (internal team) — manages content via Django admin. Adds questions, tags, manages organizations.
**Teacher** (client users) — logs in to a custom dashboard. Generates exams. Sees only their organization's data.

## App Structure
```
accounts/    # Custom user model, Organization model, login/logout, role-based redirect
questions/   # Question, Choice, Tag, TagCategory models + content management UI
exams/       # Exam generation algorithm, Exam model
dashboard/   # Teacher-facing panel, exam history
```

## Core Models

```python
class Organization(models.Model):
    name = models.CharField(max_length=200)

class User(AbstractUser):
    ROLES = [('admin', 'Admin'), ('teacher', 'Teacher')]
    role = models.CharField(max_length=20, choices=ROLES)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

class TagCategory(models.Model):
    name = models.CharField(max_length=100)  # e.g. "Grammar", "Skill", "Format"

class Tag(models.Model):
    name = models.CharField(max_length=100)  # e.g. "If Clause", "Reading", "Multiple Choice"
    category = models.ForeignKey(TagCategory, null=True, blank=True, on_delete=models.SET_NULL)

class Question(models.Model):
    LEVELS = [('A1','A1'),('A2','A2'),('B1','B1'),('B2','B2'),('C1','C1'),('C2','C2')]
    level = models.CharField(max_length=2, choices=LEVELS)
    text = models.TextField()
    image = models.ImageField(upload_to='questions/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    is_active = models.BooleanField(default=True)

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

class Exam(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    parameters = models.JSONField()   # stores level ratios, tag filters used
    questions = models.ManyToManyField(Question)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Exam Generation Logic
Teacher inputs: total question count + per-level min/max percentage ranges + optional tag filters.
Algorithm: calculate per-level counts from ratios → filter questions by level + tags → random sample → return error if not enough questions exist for given constraints.

## Question Types
All questions use the same model. Type is determined by tags (e.g. tag: "Multiple Choice", "True/False", "Fill in the Blank"). True/False = MC question with two choices. Fill in the blank = no choices, correct answer stored differently (TBD — still being decided with content team).

## Auth Flow
- Login page → check role → admin goes to /admin/, teacher goes to /dashboard/
- Teachers only see their own organization's exams
- Django session auth (no JWT, no API keys)

## Docker Setup
Two services: `django` + `postgres`. Environment variables passed via `env_file` in docker-compose. Static files served by whitenoise, media files served by nginx.

## Settings Structure
```
settings/
  base.py      # shared
  local.py     # DEBUG=True, local DB
  production.py # DEBUG=False, real SECRET_KEY, allowed hosts
```

## What Is NOT in This Project
- No REST API or API keys
- No student-facing features (planned for future)
- No CSV/Excel import (planned for future)
- No JWT or token auth
- No frontend framework (Django templates only)

---

## How to Use This File
Paste this file at the start of a new chat, then describe only the specific area you need help with. Examples:

- "Aşama 3'teyim, Question modelini admin'de inline Choice ile nasıl gösteririm?"
- "Sınav algoritmasını yazmam gerekiyor, oran motoru kısmından başlayalım."
- "Dashboard'da öğretmen sadece kendi org sınavlarını görsün, view'ı nasıl yazarım?"