from django.core.exceptions import ValidationError
from pypdf import PdfReader

MAX_PAGES = 1000


def validate_pdf(file):
    try:
        if file.size > 20 * 1024 * 1024:
            raise ValidationError("الحد الأقصى للملف 20 ميغابايت.")
        file.seek(0)
        if file.read(5) != b"%PDF-":
            raise ValidationError("يرجى رفع ملف PDF صالح.")
        file.seek(0)
        reader = PdfReader(file, strict=True)
        if reader.is_encrypted:
            raise ValidationError("الملفات المشفرة غير مدعومة.")
        if not 1 <= len(reader.pages) <= MAX_PAGES:
            raise ValidationError("عدد الصفحات المسموح من 1 إلى 1000.")
        for page in reader.pages:
            if page.get("/AA"):
                raise ValidationError("ملف PDF يحتوي على إجراءات نشطة غير مسموحة.")
        root = reader.trailer["/Root"]
        if any(k in root for k in ["/OpenAction", "/AA", "/Names"]):
            raise ValidationError("ملف PDF يحتوي على عناصر نشطة غير مدعومة.")
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("تعذر قراءة ملف PDF؛ قد يكون تالفًا.")
    finally:
        file.seek(0)


def extract_text(file):
    file.seek(0)
    reader = PdfReader(file)
    chunks = []
    total = 0
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        total += len(text)
        if total > 1500000:
            raise ValidationError("النص المستخرج كبير جدًا.")
        if text.strip():
            chunks.append(f"[صفحة {i + 1}]\n{text}")
    file.seek(0)
    if not chunks:
        raise ValidationError("لا يوجد نص قابل للاستخراج. ملفات الصور تحتاج OCR قبل الرفع.")
    return "\n\n".join(chunks)
