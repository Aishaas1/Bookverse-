from django.contrib import admin

from .models import Author, Book, Category, Comment, Discussion, Favorite, ReadingProgress, Review

admin.site.site_header = "BookVerse | إدارة المكتبة"
admin.site.site_title = "BookVerse"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "featured", "pages"]
    list_filter = ["category", "featured"]
    search_fields = ["title", "author__name"]


@admin.register(Review, Discussion, Comment)
class ModerationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "approved", "created_at"]
    list_filter = ["approved"]
    actions = ["approve", "hide"]

    @admin.action(description="نشر المحدد")
    def approve(self, request, queryset):
        queryset.update(approved=True)

    @admin.action(description="إخفاء المحدد")
    def hide(self, request, queryset):
        queryset.update(approved=False)


admin.site.register([Author, Category, Favorite, ReadingProgress])
