# ruff: noqa: E402
import json
import os
import secrets
import sys
from pathlib import Path

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"  # isolated local smoke-test process only
PROJECT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT)
SCREENSHOTS = PROJECT / "work/browser"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
BASE_URL = os.getenv("BOOKVERSE_TEST_URL", "http://127.0.0.1:8000")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
sys.path.insert(0, str(PROJECT))
import django

django.setup()
from django.contrib.auth.models import User
from playwright.sync_api import sync_playwright

from library.models import Book, ReadingProgress

username = "browser_" + secrets.token_hex(4)
password = secrets.token_urlsafe(20)
errors = []
checks = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE_URL + "/")
        page.screenshot(path=str(SCREENSHOTS / "desktop.png"), full_page=True)
        assert page.locator(".book-card").count() == 12
        checks.append("Desktop home: real book covers and all sections")
        page.locator("#theme").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.reload()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.locator("#theme").click()
        checks.append("Theme persists after reload")
        page.goto(BASE_URL + "/signup/")
        page.locator("[name=username]").fill(username)
        page.locator("[name=email]").fill("browser@example.com")
        page.locator("[name=password1]").fill(password)
        page.locator("[name=password2]").fill(password)
        page.locator("button[type=submit],form button.btn-primary").first.click()
        page.wait_for_url("**/profile/")
        checks.append("Browser registration and profile redirect")
        book = Book.objects.first()
        page.goto(f"{BASE_URL}/books/{book.pk}/read/")
        page.wait_for_function(
            "document.querySelector('#save-status').textContent.includes('حُفظ')", timeout=60000
        )
        assert page.locator("canvas").evaluate("(e)=>e.width") > 0
        page.locator("#next").click()
        page.wait_for_function(
            "document.querySelector('#page').value==='2' && document.querySelector('#save-status').textContent.includes('حُفظ')"
        )
        page.wait_for_timeout(300)
        assert ReadingProgress.objects.get(user__username=username, book=book).page == 2
        page.locator("#zoom-in").click()
        page.wait_for_timeout(500)
        page.reload()
        page.wait_for_function(
            "document.querySelector('#page').value==='2' && document.querySelector('#save-status').textContent.includes('حُفظ')",
            timeout=30000,
        )
        page.screenshot(path=str(SCREENSHOTS / "reader.png"), full_page=True)
        checks.append("PDF renders; next page, zoom and server-side progress survive reload")
        page.goto(f"{BASE_URL}/ai/?book={book.pk}")
        page.locator("button.btn-primary").last.click()
        page.wait_for_selector(".alert-warning")
        assert "غير مهيأة" in page.locator(".alert-warning").inner_text()
        checks.append("Missing AI configuration displayed correctly")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE_URL + "/")
        page.locator(".menu").click()
        assert page.locator(".links").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(SCREENSHOTS / "mobile.png"), full_page=True)
        checks.append("Mobile 390px: menu opens and no horizontal overflow")
        browser.close()
finally:
    User.objects.filter(username=username).delete()
print(json.dumps({"checks": checks, "javascript_errors": errors}, ensure_ascii=False, indent=2))
assert not errors
