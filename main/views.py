from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from django.shortcuts import redirect, render

from .models import Account


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


def dashboard(request):
    account = _get_authenticated_account(request)
    if not account:
        return redirect("auth_page")
    return render(request, "dashboard.html", {"account": account})


def logout_view(request):
    request.session.pop("account_id", None)
    return redirect("auth_page")
