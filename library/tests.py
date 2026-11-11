import io
import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from reportlab.pdfgen import canvas

from .ai import AIError, answer
from .models import (
    Author,
    Book,
    Category,
    Comment,
    Discussion,
    Document,
    Favorite,
    ReadingProgress,
    Review,
)
from .validators import validate_pdf


def pdf_bytes():
    stream = io.BytesIO()
    c = canvas.Canvas(stream)
    c.drawString(50, 700, "The book describes a journey through time.")
    c.showPage()
    c.drawString(50, 700, "The future is unknown.")
    c.save()
    return stream.getvalue()


class AppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Author.objects.create(name="ويلز")
        cls.c = Category.objects.create(name="خيال علمي")
        cls.user = User.objects.create_user("reader", "reader@example.com", "SafePassword!2026")
        cls.other = User.objects.create_user("other", password="SafePassword!2026")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.temp.name)
        self.settings_override.enable()
        self.book = Book.objects.create(
            title="آلة الزمن",
            author=self.a,
            category=self.c,
            description="رحلة",
            pdf=SimpleUploadedFile("book.pdf", pdf_bytes()),
            pages=2,
            source_url="https://www.gutenberg.org/ebooks/35",
            license="Public domain",
        )

    def tearDown(self):
        self.settings_override.disable()
        self.temp.cleanup()

    def test_public_pages_and_search(self):
        for url in [
            "/",
            "/books/",
            f"/books/{self.book.pk}/",
            "/discussions/",
            "/accounts/login/",
            "/signup/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get("/books/?q=ويلز"), "آلة الزمن")
        self.assertNotContains(self.client.get("/books/?q=missing"), "cover-link")
        self.assertContains(
            self.client.get(f"/books/?category={self.c.pk}&sort=rating"), "آلة الزمن"
        )

    def test_signup_login_profile_logout(self):
        response = self.client.post(
            "/signup/",
            {
                "username": "newreader",
                "email": "new@example.com",
                "password1": "UniquePass!78645",
                "password2": "UniquePass!78645",
            },
        )
        self.assertRedirects(response, "/profile/")
        self.client.post(
            "/profile/",
            {"first_name": "قارئ", "last_name": "جديد", "email": "edit@example.com"},
        )
        self.assertEqual(User.objects.get(username="newreader").first_name, "قارئ")
        self.client.post("/accounts/logout/")
        self.assertTrue(self.client.login(username="reader", password="SafePassword!2026"))

    def test_auth_favorite_progress_pdf_review(self):
        pk = self.book.pk
        for url in [
            "/profile/",
            "/ai/",
            f"/books/{pk}/read/",
            f"/books/{pk}/file/pdf/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/books/{pk}/favorite/").status_code, 405)
        self.client.post(f"/books/{pk}/favorite/")
        self.assertEqual(Favorite.objects.count(), 1)
        self.client.post(f"/books/{pk}/favorite/")
        self.assertEqual(Favorite.objects.count(), 0)
        self.assertEqual(self.client.get(f"/books/{pk}/read/").status_code, 200)
        self.client.post(f"/books/{pk}/progress/", {"page": 2})
        self.assertEqual(ReadingProgress.objects.get().page, 2)
        self.assertEqual(self.client.post(f"/books/{pk}/progress/", {"page": 99}).status_code, 400)
        self.assertEqual(
            self.client.post(f"/books/{pk}/progress/", {"page": "oops"}).status_code,
            400,
        )
        response = self.client.get(f"/books/{pk}/file/pdf/")
        self.assertEqual(response["Content-Type"], "application/pdf")
        response.close()
        self.client.post(f"/books/{pk}/", {"rating": 5, "body": "ممتاز"})
        self.client.post(f"/books/{pk}/", {"rating": 4, "body": "تحديث"})
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 4)
        self.client.post(f"/books/{pk}/", {"rating": 6, "body": "bad"})
        self.assertEqual(Review.objects.get().rating, 4)

    def test_discussion_reply_and_moderation(self):
        self.client.force_login(self.user)
        self.client.post(
            "/discussions/",
            {"book": self.book.pk, "title": "سؤال", "body": "ما رأيكم؟"},
        )
        discussion = Discussion.objects.get()
        url = f"/discussions/{discussion.pk}/"
        self.client.post(url, {"body": "تعليق"})
        parent = Comment.objects.get()
        self.client.post(url, {"body": "رد", "parent": parent.pk})
        self.assertEqual(Comment.objects.count(), 2)
        self.assertContains(self.client.get(url), "ردًا على")
        discussion.approved = False
        discussion.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_private_upload_and_owner_isolation(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/ai/",
            {
                "action": "upload",
                "title": "Private",
                "pdf": SimpleUploadedFile(
                    "private.pdf", pdf_bytes(), content_type="application/pdf"
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        doc = Document.objects.get()
        self.assertIn("journey", doc.text)
        self.client.force_login(self.other)
        for url in [f"/ai/?document={doc.pk}", f"/documents/{doc.pk}/file/"]:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(f"/documents/{doc.pk}/delete/").status_code, 404)
        self.client.force_login(self.user)
        with override_settings(AI_API_KEY=""):
            self.assertContains(
                self.client.post("/ai/", {"document": doc.pk, "mode": "short"}),
                "غير مهيأة",
            )
        self.client.post(f"/documents/{doc.pk}/delete/")
        self.assertFalse(Document.objects.exists())

    def test_bad_pdf_and_csrf(self):
        with self.assertRaises(ValidationError):
            validate_pdf(SimpleUploadedFile("fake.pdf", b"not a pdf"))
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.post(
                "/ai/",
                {
                    "action": "upload",
                    "title": "bad",
                    "pdf": SimpleUploadedFile("bad.pdf", b"%PDF-invalid"),
                },
            ).status_code,
            200,
        )
        self.assertFalse(Document.objects.exists())
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(f"/books/{self.book.pk}/favorite/").status_code, 403)

    @override_settings(
        AI_API_KEY="test",
        AI_BASE_URL="https://provider.example/v1",
        AI_MODEL="test-model",
    )
    @patch("library.ai.requests.post")
    def test_ai_payload_grounding_and_errors(self, post):
        post.return_value = Mock(
            json=lambda: {"choices": [{"message": {"content": "ملخص [صفحة 1]"}}]}
        )
        self.assertIn("صفحة", answer("[صفحة 1] Book text", "short"))
        payload = post.call_args.kwargs["json"]
        self.assertIn("Book text", payload["messages"][1]["content"])
        self.assertIn("النص المرفق وحده", payload["messages"][0]["content"])
        import requests

        post.side_effect = requests.Timeout()
        with self.assertRaises(AIError):
            answer("text", "short")

    @override_settings(AI_API_KEY="test")
    @patch("library.ai._complete")
    def test_long_summary_covers_all_source_pages(self, complete):
        complete.return_value = "ملخص موثق [صفحة 1]"
        source = "\n\n".join(f"[صفحة {n}]\n" + ("Book content. " * 3000) for n in range(1, 5))
        answer(source, "detailed")
        contexts = [call.args[1] for call in complete.call_args_list]
        for n in range(1, 5):
            self.assertTrue(any(f"[صفحة {n}]" in context for context in contexts))
        self.assertGreater(complete.call_count, 2)

    def test_admin_access_and_pdf_page_metadata(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.book.pages = 99
        self.book.full_clean()
        self.assertEqual(self.book.pages, 2)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.client.get("/admin/library/book/").status_code, 200)

    def test_hidden_review_cannot_be_republished_by_reader(self):
        Review.objects.create(
            user=self.user, book=self.book, rating=3, body="Hidden", approved=False
        )
        self.client.force_login(self.user)
        self.client.post(f"/books/{self.book.pk}/", {"rating": 5, "body": "Edited"})
        self.assertFalse(Review.objects.get().approved)
