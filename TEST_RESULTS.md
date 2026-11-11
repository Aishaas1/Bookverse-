# BookVerse — Executed validation

Date: 2026-11-11. Python 3.12, Django 5.2.19, SQLite, headless Chromium 158 through Playwright 1.65.0.

## نتائج الاختبارات

- Fresh source-archive installation via `bash setup.sh` succeeded: dependencies installed, random `.env` secret generated, SQLite migrated and six books seeded.
- Django migrations applied successfully; `makemigrations --check --dry-run`: no model changes missing migrations.
- `manage.py check`: no issues.
- `manage.py test -v 2`: **10 tests passed**, 0 failures, 0 errors (0.997 seconds in final functional run).
- Ruff lint and formatting checks passed.
- Seed command created six complete books, 950 generated PDF pages in total; repeated seeding does not duplicate records.

### Automated functional coverage

1. Public home, catalog, details, discussions, registration and login render; title/author search and category/rating filters work.
2. Registration, authenticated profile updates, logout and login work.
3. Reader authentication, POST-only favorites toggling, PDF serving, bounded progress persistence and unique review updates work.
4. Discussions, comments and replies work; hidden discussions return 404.
5. Valid private PDF uploads extract source text; second account cannot open the AI document, download or delete it (404).
6. Invalid PDFs are rejected and missing CSRF tokens return 403.
7. AI payload contains source text, grounding instruction and model configuration; page-cited response and provider timeout handling tested with mocked HTTP.
8. Long-document summary processes every source page through chunk/reduce flow, using a mocked provider.
9. Admin access restricted to staff; admin book listing works for superuser; PDF page metadata is computed correctly.
10. Reader cannot republish a review hidden by the administrator.

### Real browser validation (6 scenarios)

- Desktop 1440px home displays the book covers and sections.
- Theme toggle persists after reload.
- Real browser registration redirects to the personal library.
- PDF.js renders PDF pages; next page, zoom and saved progress survive reload. Database value verified as page 2.
- Unconfigured AI produces the expected Arabic message.
- Mobile 390px menu opens and the page has no horizontal overflow.

**JavaScript errors: 0.** Screenshots captured for desktop, mobile and reader. `scripts/browser_smoke.py` reproduces these scenarios against a local running server.

## حدود التحقق

No live AI provider key was supplied. Actual paid AI requests were not executed; HTTP contract, source grounding, error handling and complete-page chunking were tested with mocks. Model factual accuracy and citation quality still depend on the configured provider and should be reviewed by the reader. Long summaries can take multiple billable requests. Q&A uses basic keyword retrieval with a context cap; scanned PDFs require OCR outside this app.

## GitHub outcome

Authenticated account: `Aishaas1`. Repository creation attempted through both GraphQL (`gh repo create`) and REST (`POST /user/repos`). Both returned **Resource not accessible by integration**; REST status was **403**. No GitHub repository was created and no upload is claimed. Local Git is on `main`; source archive and portable Git bundle contain the completed project. README includes publishing instructions after obtaining sufficient GitHub permissions.
