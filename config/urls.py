from django.contrib import admin
from django.urls import include, path

from library import views as v

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("signup/", v.signup, name="signup"),
    path("", v.home, name="home"),
    path("books/", v.catalog, name="catalog"),
    path("books/<int:pk>/", v.detail, name="detail"),
    path("books/<int:pk>/favorite/", v.favorite, name="favorite"),
    path("books/<int:pk>/read/", v.reader, name="reader"),
    path("books/<int:pk>/progress/", v.progress, name="progress"),
    path("books/<int:pk>/file/<str:kind>/", v.book_file, name="book_file"),
    path("profile/", v.profile, name="profile"),
    path("ai/", v.ai, name="ai"),
    path("documents/<int:pk>/file/", v.document_file, name="document_file"),
    path("documents/<int:pk>/delete/", v.document_delete, name="document_delete"),
    path("discussions/", v.discussions, name="discussions"),
    path("discussions/<int:pk>/", v.discussion, name="discussion"),
]
