from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .ai import AIError, answer
from .forms import CommentForm, DiscussionForm, DocumentForm, ProfileForm, ReviewForm, SignupForm
from .models import Book, Category, Comment, Discussion, Document, Favorite, ReadingProgress, Review
from .validators import extract_text


def books_query():
    return Book.objects.select_related("author", "category").annotate(
        score=Avg("reviews__rating", filter=Q(reviews__approved=True)),
        readers=Count("readingprogress", distinct=True),
    )


def home(request):
    books = books_query()
    return render(
        request,
        "home.html",
        {
            "featured": books.filter(featured=True)[:4],
            "latest": books.order_by("-created_at")[:4],
            "popular": books.order_by("-readers", "-score")[:4],
            "categories": Category.objects.annotate(total=Count("book")),
            "total": books.count(),
        },
    )


def catalog(request):
    books = books_query()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "new")
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__name__icontains=q))
    if category.isdigit():
        books = books.filter(category_id=int(category))
    books = books.order_by("-score", "-id") if sort == "rating" else books.order_by("-created_at")
    return render(
        request,
        "catalog.html",
        {
            "page_obj": Paginator(books, 12).get_page(request.GET.get("page")),
            "categories": Category.objects.all(),
            "q": q,
            "selected_category": category,
            "sort": sort,
        },
    )


def detail(request, pk):
    book = get_object_or_404(books_query(), pk=pk)
    form = ReviewForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        existing = Review.objects.filter(user=request.user, book=book).first()
        form = ReviewForm(request.POST, instance=existing)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            review.save()
            messages.success(request, "حُفظت مراجعتك.")
            return redirect("detail", pk=pk)
    return render(
        request,
        "detail.html",
        {
            "book": book,
            "form": form,
            "reviews": book.reviews.filter(approved=True).select_related("user"),
            "favorite": request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, book=book).exists(),
        },
    )


@login_required
@require_POST
def favorite(request, pk):
    book = get_object_or_404(Book, pk=pk)
    obj, created = Favorite.objects.get_or_create(user=request.user, book=book)
    if not created:
        obj.delete()
    return redirect("detail", pk=pk)


@login_required
def reader(request, pk):
    book = get_object_or_404(Book, pk=pk)
    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
    return render(request, "reader.html", {"book": book, "progress": progress})


@login_required
@require_POST
def progress(request, pk):
    book = get_object_or_404(Book, pk=pk)
    try:
        page = int(request.POST.get("page", ""))
    except (TypeError, ValueError):
        return JsonResponse({"error": "رقم صفحة غير صالح"}, status=400)
    if not 1 <= page <= book.pages:
        return JsonResponse({"error": "الصفحة خارج نطاق الكتاب"}, status=400)
    ReadingProgress.objects.update_or_create(user=request.user, book=book, defaults={"page": page})
    return JsonResponse({"saved": True, "page": page})


def book_file(request, pk, kind):
    book = get_object_or_404(Book, pk=pk)
    if kind == "cover":
        file = book.cover
        content_type = "image/jpeg"
    elif kind == "pdf":
        if not request.user.is_authenticated:
            return redirect("login")
        file = book.pdf
        content_type = "application/pdf"
    else:
        raise Http404
    if not file:
        raise Http404
    response = FileResponse(file.open("rb"), content_type=content_type)
    response["Cache-Control"] = "private, no-store"
    response["Content-Security-Policy"] = "sandbox; default-src 'none'"
    return response


def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("profile")
    return render(
        request,
        "form.html",
        {"form": form, "title": "انضم إلى عالم الكتب", "submit": "إنشاء حساب"},
    )


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تم تحديث ملفك الشخصي.")
        return redirect("profile")
    return render(
        request,
        "profile.html",
        {
            "form": form,
            "favorites": Book.objects.filter(favorite__user=request.user).select_related(
                "author", "category"
            ),
            "progresses": ReadingProgress.objects.filter(user=request.user)
            .select_related("book")
            .order_by("-updated_at"),
        },
    )


def discussions(request):
    form = DiscussionForm(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("discussion", pk=obj.pk)
    return render(
        request,
        "discussions.html",
        {
            "form": form,
            "discussions": Discussion.objects.filter(approved=True)
            .select_related("book", "user")
            .order_by("-created_at"),
        },
    )


def discussion(request, pk):
    obj = get_object_or_404(Discussion, pk=pk, approved=True)
    form = CommentForm(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        if form.is_valid():
            parent = None
            if request.POST.get("parent"):
                if not request.POST["parent"].isdigit():
                    raise Http404
                parent = get_object_or_404(
                    Comment, pk=request.POST["parent"], discussion=obj, approved=True
                )
            comment = form.save(commit=False)
            comment.user = request.user
            comment.discussion = obj
            comment.parent = parent
            comment.save()
            return redirect("discussion", pk=pk)
    return render(
        request,
        "discussion.html",
        {
            "discussion": obj,
            "form": form,
            "comments": obj.comments.filter(approved=True)
            .filter(Q(parent__isnull=True) | Q(parent__approved=True))
            .select_related("user", "parent__user"),
        },
    )


@login_required
def ai(request):
    form = DocumentForm()
    result = ""
    error = ""
    document = None
    book = None
    doc_id = request.GET.get("document") or request.POST.get("document")
    book_id = request.GET.get("book") or request.POST.get("book")
    if doc_id and not doc_id.isdigit():
        raise Http404
    if book_id and not book_id.isdigit():
        raise Http404
    if doc_id:
        document = get_object_or_404(Document, pk=doc_id, owner=request.user)
    elif book_id:
        book = get_object_or_404(Book, pk=book_id)
    if request.method == "POST":
        if request.POST.get("action") == "upload":
            form = DocumentForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    text = extract_text(form.cleaned_data["pdf"])
                    obj = form.save(commit=False)
                    obj.owner = request.user
                    obj.text = text
                    obj.save()
                    return redirect("/ai/?document=" + str(obj.pk))
                except ValidationError as exc:
                    form.add_error("pdf", exc)
        else:
            try:
                if not document and not book:
                    raise AIError("اختر كتابًا أو ارفع ملفًا أولًا.")
                question = request.POST.get("question", "").strip()[:2000]
                mode = request.POST.get("mode", "short")
                if mode == "question" and not question:
                    raise AIError("اكتب سؤالك أولًا.")
                text = document.text if document else extract_text(book.pdf)
                result = answer(text, mode, question)
            except (AIError, ValidationError) as exc:
                error = str(exc)
    return render(
        request,
        "ai.html",
        {
            "form": form,
            "document": document,
            "book": book,
            "documents": Document.objects.filter(owner=request.user).order_by("-created_at"),
            "result": result,
            "error": error,
        },
    )


@login_required
def document_file(request, pk):
    doc = get_object_or_404(Document, pk=pk, owner=request.user)
    response = FileResponse(doc.pdf.open("rb"), content_type="application/pdf")
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_POST
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk, owner=request.user)
    doc.pdf.delete()
    doc.delete()
    return redirect("ai")
