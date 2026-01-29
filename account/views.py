from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from account.tokens import account_activation_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.template.loader import get_template

from .forms import (
    ProfileForm, ShopInfoForm, ShopAddressForm, ShopDocumentForm, PlanSelectionForm,
    DispatcherPersonalForm, DispatcherVehicleForm, UserRegistrationForm,
    UserEditForm, ProfileEditForm
)
from .models import Profile, Shop, DispatcherProfile

from django.contrib import messages

User = get_user_model()

# Create your views here.
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your Account'
            message = get_template('registration/account_activation_email.html').render({
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = user_form.cleaned_data.get('email')
            email = EmailMessage(
                subject, message,from_email='Bunchfood <bunchfood@gmail.com>', to=[to_email]
            )
            email.content_subtype = 'html'
            email.send()
            messages.success(request, 'An email has been sent to you,please go and activate your account')
            return redirect('home:home')
    else:
        user_form = UserRegistrationForm()
    return render(request,
                  'account/register.html',
                  {'user_form': user_form})

@login_required
def select_role(request):
    if request.method == "POST":
        role = request.POST.get("role")
        if role == "shop_owner":
            role = "shop"
        user = request.user
        user.role = role
        user.save()
        if role == "customer":
            Profile.objects.get_or_create(user=user)
            return redirect("account:customer_setup")
        elif role == "shop":
            Shop.objects.get_or_create(owner=user)
            return redirect("account:shop_info")
        elif role == "dispatcher":
            DispatcherProfile.objects.get_or_create(user=user)
            return redirect("account:dispatcher_personal")
    return render(request, "account/select_role.html")
@login_required
def edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile_display')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)
    return render(request,
                        'account/edit.html',
                        {'user_form': user_form,
                        'profile_form': profile_form})

@login_required
def profile_display(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
        return redirect('profile_display')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)
    return render(request,
                        'account/edit_display.html',
                        {'user_form': user_form,
                        'profile_form': profile_form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Your account has been confirm successfully')
        return redirect('home:home')
    else:
        messages.error(request, 'There is an error confirming your account')
        return render(request, 'registration/account_activation_invalid.html')

# -------------------------
# Choose role
# -------------------------
def choose_role(request):
    """
    After login (or immediately after activation), user chooses 'customer', 'shop', or 'dispatcher'.
    We set the user's role and redirect to the first onboarding step for that role.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role not in ('customer', 'shop', 'dispatcher'):
            messages.error(request, "Invalid role selected.")
            return redirect('account:choose_role')

        # Save role on user
        user = request.user
        user.role = role
        user.save()

        if role == 'customer':
            Profile.objects.get_or_create(user=user)
            return redirect('account:customer_setup')
        elif role == 'shop':
            Shop.objects.get_or_create(owner=user)
            # initialize shop onboarding in session
            request.session['shop_onboarding'] = {}
            return redirect('account:shop_info')
        else:
            # dispatcher
            DispatcherProfile.objects.get_or_create(user=user)
            return redirect('account:dispatcher_personal')

    return render(request, 'account/choose_role.html')


# -------------------------
# Customer simple onboarding
# -------------------------
def customer_setup(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.user.role = 'customer'
            request.user.save()
            messages.success(request, "Customer profile completed.")
            return redirect('customer:dashboard')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'account/customer_profile_setup.html', {'form': form})


# -------------------------
# Shop owner multi-step onboarding
# We'll store progress in session under 'shop_onboarding' dict.
# -------------------------
def shop_info(request):
    if not request.user.is_authenticated:
        return redirect('login')

    shop, _ = Shop.objects.get_or_create(owner=request.user)
    form = ShopInfoForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == 'POST' and form.is_valid():
        # save into session (we don't commit to DB until final step)
        # store file uploads temporarily by saving to model - simplest approach: save partial
        shop = form.save(commit=False)
        # save partial to DB so file fields persist (logo/documents)
        shop.owner = request.user
        shop.save()
        request.session['shop_onboarding'] = {'step': 'info'}
        messages.success(request, "Shop basic info saved. Continue to address.")
        return redirect('account:shop_address')

    return render(request, 'account/shop_info.html', {'form': form})


def shop_address(request):
    if not request.user.is_authenticated:
        return redirect('login')

    shop, _ = Shop.objects.get_or_create(owner=request.user)
    form = ShopAddressForm(request.POST or None, instance=shop)
    if request.method == 'POST' and form.is_valid():
        form.save()
        onboarding = request.session.setdefault('shop_onboarding', {})
        onboarding['step'] = 'address'
        request.session['shop_onboarding'] = onboarding
        messages.success(request, "Shop address saved. Continue to upload business documents (optional).")
        return redirect('account:shop_docs')

    return render(request, 'account/shop_address.html', {'form': form})


def shop_docs(request):
    if not request.user.is_authenticated:
        return redirect('login')

    shop, _ = Shop.objects.get_or_create(owner=request.user)
    form = ShopDocumentForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == 'POST' and form.is_valid():
        form.save()
        onboarding = request.session.setdefault('shop_onboarding', {})
        onboarding['step'] = 'docs'
        request.session['shop_onboarding'] = onboarding
        messages.success(request, "Document uploaded (or skipped). Continue to choose a plan.")
        return redirect('account:shop_plan')

    return render(request, 'account/shop_docs.html', {'form': form})


def shop_plan(request):
    if not request.user.is_authenticated:
        return redirect('login')

    form = PlanSelectionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        plan = form.cleaned_data.get('plan', None)
        shop, _ = Shop.objects.get_or_create(owner=request.user)
        if plan:
            shop.subscription = plan
            shop.is_active = True
            shop.save()
        else:
            # default free plan: mark shop active but no plan
            shop.is_active = True
            shop.save()

        request.user.role = 'shop'
        request.user.save()
        # clear onboarding session
        request.session.pop('shop_onboarding', None)
        messages.success(request, "Shop onboarding complete! Welcome.")
        return redirect('shop:dashboard')

    return render(request, 'account/shop_plan.html', {'form': form})


# -------------------------
# Dispatcher onboarding
# -------------------------
def dispatcher_personal(request):
    if not request.user.is_authenticated:
        return redirect('login')

    dispatcher_profile, _ = DispatcherProfile.objects.get_or_create(user=request.user)
    form = DispatcherPersonalForm(
        request.POST or None,
        request.FILES or None,
        instance=dispatcher_profile,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        request.session['dispatcher_onboarding'] = {'step': 'personal'}
        return redirect('account:dispatcher_vehicle')

    return render(request, 'account/dispatcher_personal.html', {'form': form})


def dispatcher_vehicle(request):
    if not request.user.is_authenticated:
        return redirect('login')

    dispatcher_profile, _ = DispatcherProfile.objects.get_or_create(user=request.user)
    form = DispatcherVehicleForm(request.POST or None, instance=dispatcher_profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        # mark as pending review
        dispatcher_profile.status = 'pending'
        dispatcher_profile.save()
        request.user.role = 'dispatcher'
        request.user.save()
        messages.success(request, "Dispatcher application submitted and is pending admin approval.")
        return redirect('dispatcher:pending')  # a page informing them of pending review

    return render(request, 'account/dispatcher_vehicle.html', {'form': form})
