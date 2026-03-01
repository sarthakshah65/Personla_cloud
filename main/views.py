import math
import os
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import FileResponse, Http404

from .models import Account, Upload

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024 * 1024


def _get_authenticated_account(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return None
    return Account.objects.filter(pk=account_id).first()

def landing_page(request):
    return render(request, "index.html")


def auth_page(request):
    context = {
        "login_status": None,
        "login_message": "",
        "signup_status": None,
        "signup_message": "",
    }

    if _get_authenticated_account(request):
        return redirect("dashboard")

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "login":
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")

            errors = []

            if not email:
                errors.append("Email is required.")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters.")

            if not errors:
                account = Account.objects.filter(email=email).first()
                if not account:
                    errors.append("No account matches that email.")
                elif not check_password(password, account.password):
                    errors.append("Invalid email or password.")
                else:
                    request.session["account_id"] = account.pk
                    return redirect("dashboard")

            if errors:
                context["login_status"] = "error"
                context["login_message"] = " ".join(errors)

        elif form_type == "signup":
            full_name = request.POST.get("full_name", "").strip()
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")

            errors = []

            if len(full_name) < 2:
                errors.append("Full name must be at least 2 characters.")
            if not email:
                errors.append("Email is required.")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters.")

            if not errors:
                try:
                    Account.objects.create(
                        full_name=full_name,
                        email=email,
                        password=make_password(password),
                    )
                    context["signup_status"] = "success"
                    context["signup_message"] = "Account created. You can sign in now."
                except IntegrityError:
                    context["signup_status"] = "error"
                    context["signup_message"] = "An account with that email already exists."
            else:
                context["signup_status"] = "error"
                context["signup_message"] = " ".join(errors)

    return render(request, "auth.html", context)


@never_cache
def dashboard(request):
    account = _get_authenticated_account(request)
    if not account:
        return redirect("auth_page")

    upload_errors = []
    upload_form_data = {
        "title": "",
        "category": "",
        "visibility": Upload.Visibility.PRIVATE,
    }

    if request.method == "POST":
        file_obj = request.FILES.get("file")
        title = request.POST.get("title", "").strip()
        category = request.POST.get("category", "").strip()
        visibility = request.POST.get("visibility") or Upload.Visibility.PRIVATE
        visibility_choices = {choice[0] for choice in Upload.Visibility.choices}

        if not file_obj:
            upload_errors.append("Choose a file to upload.")
        if not title and file_obj:
            title = file_obj.name
        if not title:
            upload_errors.append("Provide a title for the upload.")
        elif len(title) < 3:
            upload_errors.append("Title must be at least 3 characters.")
        if len(category) > 64:
            upload_errors.append("Category must be 64 characters or fewer.")
        if visibility not in visibility_choices:
            visibility = Upload.Visibility.PRIVATE
        if file_obj and file_obj.size > MAX_UPLOAD_SIZE_BYTES:
            upload_errors.append("Files must be 5 GB or smaller.")

        upload_form_data = {
            "title": title,
            "category": category,
            "visibility": visibility,
        }

        if not upload_errors:
            size_mb = max(1, math.ceil(file_obj.size / (1024 * 1024)))
            now = timezone.now()
            upload = Upload.objects.create(
                account=account,
                title=title,
                category=category or "General",
                visibility=visibility,
                size_mb=size_mb,
                file=file_obj,
                status=Upload.Status.SYNCED,
                synced_at=now,
            )
            messages.success(request, f'"{upload.title}" is synced and ready.')
            return redirect("dashboard")

    uploads = account.uploads.all()
    total_size_mb = uploads.aggregate(total=Sum("size_mb"))["total"] or 0
    storage_used_gb = total_size_mb / 1024
    uploads_total_size_gb = round(storage_used_gb, 1)
    week_ago = timezone.now() - timedelta(days=7)
    storage_percentage = round(
        (storage_used_gb / account.storage_quota_gb) * 100, 1
    ) if account.storage_quota_gb else 0
    uploads_queued = uploads.filter(status=Upload.Status.QUEUED).count()
    uploads_processing = uploads.filter(status=Upload.Status.PROCESSING).count()
    uploads_total_count = uploads.count()
    stats = {
        "storage_used_gb": storage_used_gb,
        "storage_quota_gb": account.storage_quota_gb,
        "storage_percentage": storage_percentage,
        "uploads_total_size_gb": uploads_total_size_gb,
        "uploads_total_count": uploads_total_count,
        "uploads_queued": uploads_queued,
        "uploads_processing": uploads_processing,
        "recent_activity_count": uploads.filter(updated_at__gte=week_ago).count(),
        "uploads_complete": uploads.filter(status=Upload.Status.SYNCED).count(),
        "links_ready": uploads.filter(has_public_link=True).count(),
        "security_profile": account.security_profile,
        "plan_name": account.plan_name,
        "recent_uploads": uploads.order_by("-updated_at"),
        "upload_errors": upload_errors,
        "upload_form_data": upload_form_data,
        "visibility_choices": Upload.Visibility.choices,
    }
    return render(request, "dashboard.html", {"account": account, "stats": stats})


def logout_view(request):
    print("Hello world")
    request.session.pop("account_id", None)
    return redirect("auth_page")


def download_upload(request, upload_id):
    account = _get_authenticated_account(request)
    if not account:
        return redirect("auth_page")

    upload = Upload.objects.filter(pk=upload_id, account=account).first()
    if not upload or not upload.file:
        raise Http404("No file found for download.")

    file_handle = upload.file.open("rb")
    filename = os.path.basename(upload.file.name)
    return FileResponse(file_handle, as_attachment=True, filename=filename)
