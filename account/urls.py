from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path(
        'login/',
        views.AccountLoginView.as_view(),
        name='login'
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # change password urls
    path('password_change/',
        auth_views.PasswordChangeView.as_view(),
        name='password_change'),
    path('password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),

    # reset password urls
    path('password_reset/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'),
    path('password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'),
    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'),

    path('register/', views.register, name='register'),

    path('edit/', views.edit, name='edit'),
    path('profile_display/', views.profile_display, name='profile_display'),

    re_path(
        r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$',
        views.activate,
        name='activate',
    ),
    path('choose-role/', views.choose_role, name='choose_role'),
    path('customer/setup/', views.customer_setup, name='customer_setup'),

    # Shop onboarding multi-step
    path('shop/info/', views.shop_info, name='shop_info'),
    path('shop/address/', views.shop_address, name='shop_address'),
    path('shop/docs/', views.shop_docs, name='shop_docs'),
    path('shop/plan/', views.shop_plan, name='shop_plan'),

    # Dispatcher onboarding
    path('dispatcher/personal/', views.dispatcher_personal, name='dispatcher_personal'),
    path('dispatcher/vehicle/', views.dispatcher_vehicle, name='dispatcher_vehicle'),
]
