from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from .models import Profile, Category
from django.db.models import Count, Sum
from django.contrib.auth.decorators import login_required


def home_view(request):
    return render(request, 'dashboard.html')


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "info":
            request.user.first_name = request.POST.get("first_name")
            request.user.last_name = request.POST.get("last_name")
            request.user.email = request.POST.get("email")
            request.user.username = request.POST.get("email")
            request.user.save()

            profile.monthly_budjet = request.POST.get("monthly_budget") or 0
            profile.save()
            messages.success(request, "Profil ma'lumotlari muvaffaqiyatli yangilandi.")

        elif action == "password":
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            new_password2 = request.POST.get("new_password_confirm")

            if not request.user.check_password(current_password):
                messages.error(request, "Joriy parol noto'g'ri!")
            elif new_password != new_password2:
                messages.error(request, "Yangi parollar bir-biriga mos kelmadi!")
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # tizimdan chiqib ketmaslik uchun
                messages.success(request, "Parol muvaffaqiyatli yangilandi.")

        elif action == "delete":
            if request.user.check_password(request.POST.get("confirm_password")):
                request.user.delete()
                logout(request)
                return redirect("main:login_sahifa")
            messages.error(request, "Parol noto'g'ri!")

        return redirect("main:profile_sahifa")

    return render(request, 'profile.html', {"profile": profile})


@login_required
def categories(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Category.objects.create(category_name=name, user_account=request.user)
        messages.success(request, "Kategoriya qo'shildi.")
        return redirect("main:categoriya_sahifa")

    categories = Category.objects.filter(user_account=request.user).annotate(
        expense_count=Count('expanse'), expense_total=Sum('expanse__amount'))
    return render(request, 'categories.html', {"categories": categories})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, id=pk, user_account=request.user)

    if request.method == "POST":
        category.category_name = request.POST.get("name")
        category.save()
        messages.success(request, "Kategoriya yangilandi.")
        return redirect("main:categoriya_sahifa")

    categories = Category.objects.filter(user_account=request.user).annotate(
        expense_count=Count('expanse'), expense_total=Sum('expanse__amount'))
    return render(request, 'categories.html', {"categories": categories, "edit_category": category})


@login_required
def category_delete(request, pk):
    if request.method == "POST":
        category = get_object_or_404(Category, id=pk, user_account=request.user)
        category.delete()
        messages.success(request, "Kategoriya o'chirildi.")
    return redirect("main:categoriya_sahifa")


def expenses_form(request):
    return render(request, 'expense_form.html')


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("main:home_sahifa")
        messages.error(request, "Login yoki parol noto'g'ri kiritildi.")

    return render(request, 'login.html')


def register(request):
    if request.method == "POST":
        name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        consent = request.POST.get("consent") == "on"

        if password != password2:
            messages.error(request, "Parollar bir-biriga mos kelmadi!")
            return redirect("main:register_sahifa")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Siz bu emaildan allaqachon ro'yxatdan o'tgansiz!")
            return redirect("main:register_sahifa")

        new_user = User.objects.create_user(
            first_name=name,
            last_name=last_name,
            username=email,
            email=email,
            password=password
        )

        Profile.objects.create(
            consent=consent,
            user=new_user
        )

        messages.success(request, "Siz muvaffaqqiyatli ro'yxatdan o'tdingiz!")
        return redirect("main:login_sahifa")

    return render(request, 'register.html')


def expenses(request):
    return render(request, 'expenses.html')