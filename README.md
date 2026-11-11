# BookVerse — المكتبة الذكية التفاعلية

A working Arabic RTL library built with Python, Django 5.2, SQLite, Django Templates, Bootstrap 5, and local PDF.js. Includes six full public-domain English classics, original covers, reader progress, favorites, reviews, discussions/replies, private PDF uploads and an OpenAI-compatible reading assistant.

## التشغيل بالعربية

المتطلبات: Python 3.12+ وGit. يعمل على Linux/macOS، وعلى Windows عبر الأوامر اليدوية أدناه (استبدل `.venv/bin/python` بـ `.venv\Scripts\python`).

```bash
git clone https://github.com/Aishaas1/Bookverse-.git BookVerse
cd BookVerse
bash setup.sh
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

افتح http://127.0.0.1:8000 وواجهة الإدارة http://127.0.0.1:8000/admin/ . أنشئ حساب قارئ من الموقع. لا توجد كلمات مرور تجريبية ثابتة. ينشئ `setup.sh` ملف `.env` بسر عشوائي، ويطبق migrations ويحمل الكتب المضمّنة دون شبكة بعد تثبيت المتطلبات.

الواجهة عربية والكتب الستة التجريبية كاملة باللغة الإنجليزية. يمكن للمدير إضافة كتب عربية مرخّصة من لوحة الإدارة، مع الغلاف والملف والمصدر والترخيص. لا يضيف المشروع تقييمات أو مستخدمين وهميين. تبدأ المناقشات والمراجعات بمشاركات المستخدمين الفعلية.

## Quick start / manual setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# Set a random SECRET_KEY in .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

`seed_demo` is idempotent. It copies the bundled licensed PDFs to private storage and adds their metadata. SQLite and private uploads are deliberately excluded from Git; every clone recreates the library with this command. See `demo/manifest.json` for metadata and sources.

## الذكاء الاصطناعي / AI setup

اضبط القيم التالية في `.env` ثم أعد تشغيل الخادم. لا تشارك المفاتيح في Git أو في المحادثة.

```dotenv
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_API_KEY=your-provider-key
```

Any provider implementing `POST /chat/completions` can be used. The app extracts text with pypdf, offers short/detailed summaries, key ideas, review questions and content Q&A. It sends source text and asks for page citations and abstention if evidence is missing. Missing configuration and network/provider failures produce clear Arabic messages, without fabricated answers. Long-book summaries cover the complete extracted text with page-preserving chunks and hierarchical map/reduce (up to three concurrent provider requests). This makes multiple billable requests and may take several minutes. Q&A uses page retrieval by keyword overlap and a 45,000-character context limit; the model is instructed to disclose incomplete context. Keyword retrieval works best when the question uses terms from the source language. This is basic retrieval, not a guarantee of exhaustive or error-free answers. Scanned PDFs require external OCR first.

الملفات الخاصة لا تظهر إلا لصاحب الحساب. عند استخدام AI ترسل مقتطفات إلى المزود الذي تضبطه، وقد تطبق عليه رسوم وسياسة خصوصية خاصة. الاختبارات تتحقق من التكامل بمحاكاة المزود؛ لا توجد مفاتيح في بيئة التطوير ولم نختبر طلبًا مدفوعًا حقيقيًا.

## Features and structure

- `config/`: settings, URLs, WSGI.
- `library/`: ORM models, forms, permissions, PDF validation, AI adapter, admin, migrations, tests.
- `templates/`, `static/`: Arabic responsive UI, light/dark mode persisted locally, Bootstrap RTL and vendored PDF.js.
- `demo/`: complete original source texts, generated reading PDFs, source manifest. Full Gutenberg notices are preserved.
- Django User + Authors, Categories, Books, Favorites, ReadingProgress, Reviews, Discussions, Comments; additional owner-scoped Document model.
- Protected PDF reader: page controls, zoom, server-side last-page persistence, favorites. PDF.js renders canvas without running PDF JavaScript.
- One review and one favorite/progress row per user/book, database constraints, rating/page bounds, CSRF-protected writes, safe template escaping, POST logout.
- Admin supports covers/PDF uploads, users/categories/authors and moderation via approval flags and actions. Hidden discussions/comments/reviews disappear from public pages. Uploaded private documents intentionally are not exposed in admin.
- Uploads: 20 MB, maximum 1,000 pages, valid PDF signature/parser, no encrypted documents or active root actions; no direct public media route. Private files use UUID names and owner checks. Apply infrastructure request limits and malware scanning for public deployments.

## الاختبار / Tests

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test -v 2
```

See `TEST_RESULTS.md` for the actual executed results. Optional browser checks require `requirements-dev.txt`, Playwright Chromium and the development server. To reproduce browser validation with the server running locally:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/browser_smoke.py
```

Set `BOOKVERSE_TEST_URL` to use a different local port. Browser screenshots are written to the ignored `work/browser/` directory. Browser smoke validation expects the six demo books and no configured AI key. Test accounts are created only in the temporary test database or browser session and removed after validation.

## Production

Use a production WSGI server, HTTPS, `DEBUG=False`, a strong `SECRET_KEY` and exact `ALLOWED_HOSTS`. Run `collectstatic` and serve **only** `staticfiles/` publicly. Never expose `private-media/` through the web server. Back up SQLite and private storage together. Configure reverse-proxy upload limits, account/AI rate limits, provider budget limits and monitoring before opening public registration. SQLite is appropriate for a small single-node deployment; use PostgreSQL for larger concurrent workloads. Development `runserver` is for local use.

## Licenses / تراخيص المحتوى

The six bundled books are public domain in the United States according to Project Gutenberg. Copyright status differs by jurisdiction; verify local law before redistribution or deployment. Source notices are preserved in the text and generated PDFs. BookVerse covers are original SVG designs; they are not historical publisher covers. No third-party modern commercial books are bundled. See `demo/SOURCES.md` and `THIRD_PARTY.md`.

Application code and original cover artwork: MIT (`LICENSE`). Third-party books and libraries retain their own terms.

## GitHub / المستودع

Source repository: https://github.com/Aishaas1/Bookverse- — branch `main`.

اسم المشروع BookVerse، واسم المستودع الذي اختاره صاحب المشروع هو `Bookverse-`. ملفات التشغيل والمحتوى التجريبي مضمنة، بينما مفاتيح API وقاعدة البيانات المحلية والملفات الخاصة مستبعدة من Git.
