import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_pdf


def private_path(instance, filename):
    return f"uploads/{uuid.uuid4()}.pdf"


class Author(models.Model):
    name = models.CharField(max_length=180)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=220)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    cover = models.ImageField(upload_to="covers/", blank=True)
    cover_art = models.CharField(max_length=200, blank=True)
    pdf = models.FileField(upload_to=private_path, validators=[validate_pdf])
    source_url = models.URLField()
    license = models.CharField(max_length=250)
    featured = models.BooleanField(default=False)
    pages = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.pdf:
            from pypdf import PdfReader

            validate_pdf(self.pdf)
            self.pages = len(PdfReader(self.pdf).pages)
            self.pdf.seek(0)

    def __str__(self):
        return self.title


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_favorite")]


class ReadingProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    page = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def percent(self):
        return min(100, round(self.page / self.book.pages * 100))

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_progress")]


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    body = models.TextField(max_length=3000)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_review")]


class Discussion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=5000)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField(max_length=3000)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    pdf = models.FileField(upload_to=private_path, validators=[validate_pdf])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
