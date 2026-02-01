from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('social-auth/',include('social_django.urls', namespace='social')),
    path('foodcreate/',include('foodCreate.urls', namespace='foodcreate')),
    path('blog/',include('blog.urls', namespace='blog')),
    path('marketing/',include('marketing.urls', namespace='marketing')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('budget/', include('budget.urls', namespace='budget')),
    path('order/',include('order.urls', namespace='order')),
    path('owner/',include('owner.urls', namespace='owner')),
    path('voice/', include('voice.urls', namespace='voice')),
    path('',include('home.urls', namespace='home')),
    path('product_search/',include('search.urls', namespace='product_search')),
    path('hitcount/', include(('hitcount.urls', 'hitcount'), namespace='hitcount')),
    # path('tracking/', include('tracking.urls')),
    path('ratings/', include('star_ratings.urls', namespace='ratings')),
    path("paystack/", include(('django_paystack.urls','paystack'),namespace='paystack')),
    path('ckeditor/', include('ckeditor_uploader.urls')),

]
if settings.DEBUG:urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
