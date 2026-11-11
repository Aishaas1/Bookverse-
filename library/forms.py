from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Comment, Discussion, Document, Review


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label="البريد الإلكتروني")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "body"]
        labels = {"rating": "التقييم من 1 إلى 5", "body": "مراجعتك"}


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ["book", "title", "body"]
        labels = {"book": "الكتاب", "title": "عنوان المناقشة", "body": "ابدأ الحوار"}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        labels = {"body": "تعليقك"}


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "pdf"]
        labels = {"title": "اسم الكتاب", "pdf": "ملف PDF (حتى 20 MB)"}
