from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Category, Products, ProductsImages, SubCategory, ReviewRating, User


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name','slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title','price','slug',
    'available', 'created_at', 'updated_at']
    list_filter = ['available', 'created_at', 'updated_at']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(SubCategory)
admin.site.register(ProductsImages)
admin.site.register(ReviewRating)