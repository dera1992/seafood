from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from geopy.geocoders import Nominatim
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

if settings.GIS_ENABLED:
    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point
else:
    gis_models = None


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('pending', 'Pending'),
        ('customer', 'Customer'),
        ('shop', 'Shop Owner'),
        ('dispatcher', 'Dispatcher'),
    )
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='pending')


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No username required

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Profile(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255,null=True,blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='profile/%Y/%m/%d/',blank=True, default='profile/None/avater.png')
    active = models.BooleanField(default=True,blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.email

    # @property
    # def fullname(self):
    #     return "{} {}".format(self.first_name, self.last_name)

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_limit = models.PositiveIntegerField(default=10)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Shop(models.Model):
    WEIGHT_UNIT_CHOICES = (
        ("kg", "Kilogram (kg)"),
        ("g", "Gram (g)"),
        ("lb", "Pound (lb)"),
        ("oz", "Ounce (oz)"),
        ("unit", "Unit"),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    logo = models.ImageField(upload_to="shops/logos/", blank=True)
    currency = models.CharField(max_length=8, default="NGN")
    weight_unit = models.CharField(max_length=10, choices=WEIGHT_UNIT_CHOICES, default="kg")

    if settings.GIS_ENABLED:
        location = gis_models.PointField(geography=True, srid=4326, blank=True, null=True)
    else:
        location = models.CharField(max_length=255, blank=True, null=True)

    # Opening hours
    open_time = models.TimeField(default="08:00")
    close_time = models.TimeField(default="20:00")
    is_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)

    # business proof documents
    business_document = models.FileField(upload_to='shops/documents/', blank=True, null=True)

    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_shop_open(self):
        now = timezone.localtime().time()
        return self.open_time <= now <= self.close_time and self.is_open

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if settings.GIS_ENABLED:
            if self.latitude is not None and self.longitude is not None:
                self.location = Point(float(self.longitude), float(self.latitude), srid=4326)
            elif not self.location and self.address and self.city and self.country:
                geolocator = Nominatim(user_agent="ecommerce_app")
                location = geolocator.geocode(f"{self.address}, {self.city}, {self.country}")
                if location:
                    self.location = Point(location.longitude, location.latitude, srid=4326)
        super().save(*args, **kwargs)


class ShopSubscription(models.Model):
    shop = models.OneToOneField('Shop', on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def is_active(self):
        return self.active and self.end_date and self.end_date >= timezone.now()

    def __str__(self):
        return f"{self.shop.name} - {self.plan.name if self.plan else 'No Plan'}"

class DispatcherProfile(models.Model):
    STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dispatcher_profile')
    full_name = models.CharField(max_length=255, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    vehicle_type = models.CharField(max_length=100, blank=True)
    plate_number = models.CharField(max_length=50, blank=True)
    id_document = models.FileField(upload_to='dispatchers/documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    def __str__(self):
        return f"Dispatcher: {self.user.email} ({self.status})"


class ShopFollower(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shop_following")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "shop"], name="unique_shop_follower"),
        ]

    def __str__(self):
        return f"{self.user.email} follows {self.shop.name}"


class ShopNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shop_notifications")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="notifications")
    product = models.ForeignKey("foodCreate.Products", on_delete=models.CASCADE, related_name="shop_notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.shop.name} - {self.product.title}"


class ShopIntegration(models.Model):
    PROVIDER_CHOICES = (
        ("shopify", "Shopify"),
        ("square", "Square"),
        ("quickbooks", "QuickBooks"),
    )

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="integrations")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    access_token = models.CharField(max_length=255, blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)
    external_store_id = models.CharField(max_length=255, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default="pending")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["shop", "provider"], name="unique_shop_provider"),
        ]

    def __str__(self):
        return f"{self.shop.name} - {self.provider}"
