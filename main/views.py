from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib import messages
from .models import Profile, Category
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
def home_view(request):
    return render(request, 'dashboard.html')



@login_required
def profile(request):
    user = request.user
    prof, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "info":
            first_name = (request.POST.get("first_name") or "").strip()
            last_name = (request.POST.get("last_name") or "").strip()
            email = (request.POST.get("email") or "").strip().lower()
            try:
                budget = int(request.POST.get("monthly_budget") or 0)
            except ValueError:
                budget = -1

            if not (first_name and last_name and email):
                messages.error(request, "Ism, familiya va e-mail majburiy.")
            elif budget < 0:
                messages.error(request, "Oylik byudjet musbat son bo'lishi kerak.")
            elif User.objects.filter(username=email).exclude(pk=user.pk).exists():
                messages.error(request, "Bu e-mail boshqa hisobga tegishli.")
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.username = email
                user.save()
                prof.monthly_budjet = budget
                prof.save()
                messages.success(request, "Profil ma'lumotlari muvaffaqiyatli yangilandi.")
            return redirect("main:profile_sahifa")

        if action == "password":
            current = request.POST.get("current_password") or ""
            new = request.POST.get("new_password") or ""
            new2 = request.POST.get("new_password_confirm") or ""
            if not user.check_password(current):
                messages.error(request, "Joriy parol noto'g'ri.")
            elif new != new2:
                messages.error(request, "Yangi parollar bir-biriga mos kelmadi.")
            else:
                try:
                    validate_password(new, user=user)
                except ValidationError as e:
                    messages.error(request, " ".join(e.messages))
                else:
                    user.set_password(new)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Parol muvaffaqiyatli yangilandi.")
            return redirect("main:profile_sahifa")

        if action == "delete":
            if user.check_password(request.POST.get("confirm_password") or ""):
                logout(request)
                user.delete()
                messages.success(request, "Hisobingiz o'chirildi.")
                return redirect("main:login_sahifa")
            messages.error(request, "Hisobni o'chirish uchun parolni to'g'ri kiriting.")
            return redirect("main:profile_sahifa")

    return render(request, 'profile.html', {"profile": prof})

def _categories_qs(user):
    return (
        Category.objects.filter(user_account=user)
        .annotate(expense_count=Count('expanse'), expense_total=Sum('expanse__amount'))
        .order_by('category_name')
    )


@login_required
def categories(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "Kategoriya nomini kiriting.")
        elif Category.objects.filter(user_account=request.user, category_name__iexact=name).exists():
            messages.error(request, "Bunday nomli kategoriya allaqachon mavjud.")
        else:
            Category.objects.create(user_account=request.user, category_name=name[:100])
            messages.success(request, "Kategoriya qo'shildi.")
            return redirect("main:categoriya_sahifa")
    return render(request, 'categories.html', {"categories": _categories_qs(request.user)})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, user_account=request.user)
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "Kategoriya nomini kiriting.")
        elif Category.objects.filter(user_account=request.user, category_name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, "Bunday nomli kategoriya allaqachon mavjud.")
        else:
            category.category_name = name[:100]
            category.save()
            messages.success(request, "Kategoriya yangilandi.")
            return redirect("main:categoriya_sahifa")
    return render(request, 'categories.html', {
        "categories": _categories_qs(request.user),
        "edit_category": category,
    })


@login_required
@require_POST
def category_delete(request, pk):
    get_object_or_404(Category, pk=pk, user_account=request.user).delete()
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
            consent = consent,
            user=new_user 
        )

        messages.success(request, "Siz muvaffaqqiyatli ro'yxatdan o'tdingiz!")
        return redirect("main:login_sahifa")

    return render(request, 'register.html')


def expenses(request):
    return render(request, 'expenses.html')
