from django.contrib import admin
from django.conf import settings
from .models import (
    DispatcherProfile,
    Profile,
    Shop,
    ShopSubscription,
    SubscriptionPlan,
    ShopFollower,
    ShopNotification,
)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import User


class UserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'role', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(User, UserAdmin)



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user' ,'phone', 'photo']


if settings.GIS_ENABLED:
    from django.contrib.gis.admin import GISModelAdmin

    ShopAdminBase = GISModelAdmin
else:
    ShopAdminBase = admin.ModelAdmin


@admin.register(Shop)
class ShopAdmin(ShopAdminBase):
    list_display = ['name', 'owner', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['name', 'owner__email']


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'vehicle_type', 'plate_number']
    list_filter = ['status']
    search_fields = ['user__email', 'full_name', 'id_number']


@admin.register(ShopSubscription)
class ShopSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['shop', 'plan', 'active', 'start_date', 'end_date']
    list_filter = ['active', 'plan']
    search_fields = ['shop__name']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'product_limit', 'duration_days']
    search_fields = ['name']


@admin.register(ShopFollower)
class ShopFollowerAdmin(admin.ModelAdmin):
    list_display = ["user", "shop", "created_at"]
    search_fields = ["user__email", "shop__name"]
    list_filter = ["created_at"]


@admin.register(ShopNotification)
class ShopNotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "shop", "product", "created_at", "is_read"]
    search_fields = ["user__email", "shop__name", "product__title"]
    list_filter = ["created_at", "is_read"]
