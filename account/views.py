from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from account.tokens import account_activation_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.core.mail import EmailMessage, send_mail
from django.template.loader import get_template

from .forms import (
    ProfileForm, ShopInfoForm, ShopAddressForm, ShopDocumentForm, PlanSelectionForm,
    DispatcherPersonalForm, DispatcherVehicleForm, UserRegistrationForm,
    UserEditForm, ProfileEditForm, EmailAuthenticationForm
)
from .models import Profile, Shop, DispatcherProfile

from django.contrib import messages

User = get_user_model()

# Create your views here.
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request=request)
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
        user_form = UserRegistrationForm(request=request)
    return render(request,
                  'account/register.html',
                  {
                      'user_form': user_form,
                      'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                  })


class AccountLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = EmailAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recaptcha_site_key'] = settings.RECAPTCHA_SITE_KEY
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        return response

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
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Your account has been confirm successfully')
        return redirect('choose_role')
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
            return redirect('choose_role')

        # Save role on user
        user = request.user
        user.role = role
        user.save()

        if role == 'customer':
            Profile.objects.get_or_create(user=user)
            return redirect('customer_setup')
        elif role == 'shop':
            Shop.objects.get_or_create(owner=user)
            # initialize shop onboarding in session
            request.session['shop_onboarding'] = {}
            return redirect('shop_info')
        else:
            # dispatcher
            DispatcherProfile.objects.get_or_create(user=user)
            return redirect('dispatcher_personal')

    return render(request, 'account/choose_role.html')


# -------------------------
# Customer simple onboarding
# -------------------------
def customer_setup(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'GET' and request.GET.get('skip') == '1':
        request.user.role = 'customer'
        request.user.save()
        messages.info(request, "You can complete your profile any time from your account settings.")
        return redirect('home:dashboard')
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.user.role = 'customer'
            request.user.save()
            messages.success(request, "Customer profile completed.")
            return redirect('home:dashboard')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'account/customer_profile_setup.html', {'form': form})


# -------------------------
# Shop owner multi-step onboarding
# We'll store progress in session under 'shop_onboarding' dict.
# -------------------------
def shop_onboarding(request, step='info'):
    if not request.user.is_authenticated:
        return redirect('login')

    steps = ['info', 'address', 'docs', 'plan']
    if step not in steps:
        step = 'info'

    shop, _ = Shop.objects.get_or_create(owner=request.user)
    form_map = {
        'info': ShopInfoForm(request.POST or None, request.FILES or None, instance=shop),
        'address': ShopAddressForm(request.POST or None, instance=shop),
        'docs': ShopDocumentForm(request.POST or None, request.FILES or None, instance=shop),
        'plan': PlanSelectionForm(request.POST or None),
    }
    form = form_map[step]

    if request.method == 'POST' and form.is_valid():
        if step == 'info':
            shop = form.save(commit=False)
            shop.owner = request.user
            shop.save()
            messages.success(request, "Shop basic info saved. Continue to address.")
        elif step == 'address':
            form.save()
            messages.success(request, "Shop address saved. Continue to upload business documents (optional).")
        elif step == 'docs':
            form.save()
            messages.success(request, "Document uploaded (or skipped). Continue to choose a plan.")
        elif step == 'plan':
            plan = form.cleaned_data.get('plan', None)
            if plan:
                shop.subscription = plan
            shop.is_active = True
            shop.save()

            admin_emails = list(
                User.objects.filter(is_staff=True, is_superuser=True)
                .exclude(email="")
                .values_list("email", flat=True)
            )
            if admin_emails:
                send_mail(
                    "New shop account opened",
                    (
                        f"A new shop account has been opened.\n\n"
                        f"Shop: {shop.name}\n"
                        f"Owner: {request.user.email}\n"
                        f"Shop ID: {shop.id}"
                    ),
                    getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@seafood.local"),
                    admin_emails,
                    fail_silently=True,
                )

            request.user.role = 'shop'
            request.user.save()
            request.session.pop('shop_onboarding', None)
            messages.success(request, "Shop onboarding complete! Welcome.")
            messages.warning(
                request,
                "Your shop account has been submitted. Activation can take up to 24 hours.",
            )
            return redirect('home:dashboard')

        current_index = steps.index(step)
        request.session['shop_onboarding'] = {'step': step}
        next_step = steps[current_index + 1]
        next_map = {
            'info': 'shop_address',
            'address': 'shop_docs',
            'docs': 'shop_plan',
        }
        return redirect(next_map.get(step, 'shop_info'))

    current_index = steps.index(step)
    progress_percent = int(((current_index + 1) / len(steps)) * 100)
    step_labels = {
        'info': 'Shop Info',
        'address': 'Address',
        'docs': 'Documents',
        'plan': 'Plan',
    }
    step_urls = {
        'info': reverse('shop_info'),
        'address': reverse('shop_address'),
        'docs': reverse('shop_docs'),
        'plan': reverse('shop_plan'),
    }
    step_items = [
        {
            'key': step_key,
            'label': step_labels[step_key],
            'is_current': step_key == step,
            'is_complete': index < current_index,
            'url': step_urls[step_key],
        }
        for index, step_key in enumerate(steps)
    ]
    prev_url = step_urls[steps[current_index - 1]] if current_index > 0 else None

    return render(
        request,
        'account/shop_onboarding.html',
        {
            'form': form,
            'step_items': step_items,
            'current_step': step,
            'progress_percent': progress_percent,
            'prev_url': prev_url,
        },
    )


def shop_info(request):
    return shop_onboarding(request, step='info')


def shop_address(request):
    return shop_onboarding(request, step='address')


def shop_docs(request):
    return shop_onboarding(request, step='docs')


def shop_plan(request):
    return shop_onboarding(request, step='plan')


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
        return redirect('dispatcher_vehicle')

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
        return redirect('home:dashboard')  # a page informing them of pending review

    return render(request, 'account/dispatcher_vehicle.html', {'form': form})
