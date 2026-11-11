from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from pypdf import PdfReader

from library.models import Author, Book, Category


class Command(BaseCommand):
    help = "Load bundled public-domain books; safe to repeat, no network required."

    def handle(self, *args, **options):
        import json

        data = json.loads((settings.BASE_DIR / "demo/manifest.json").read_text())
        for item in data:
            if Book.objects.filter(title=item["title"]).exists():
                continue
            author, _ = Author.objects.get_or_create(name=item["author"])
            category, _ = Category.objects.get_or_create(name=item["category"])
            pdf = (settings.BASE_DIR / "demo" / item["file"]).read_bytes()
            book = Book(
                title=item["title"],
                author=author,
                category=category,
                description=item["description"],
                source_url=item["source"],
                license="ملكية عامة في الولايات المتحدة — Project Gutenberg. تحقق من قوانين بلدك قبل إعادة التوزيع.",
                featured=item["featured"],
                cover_art=item["cover"],
                pages=len(PdfReader(settings.BASE_DIR / "demo" / item["file"]).pages),
            )
            book.pdf.save(item["file"], ContentFile(pdf), save=True)
        self.stdout.write(self.style.SUCCESS(f"Library ready: {Book.objects.count()} books"))
