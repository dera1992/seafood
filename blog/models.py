from __future__ import unicode_literals


from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
# from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from account.models import Profile, User
from django.dispatch import receiver
from ckeditor_uploader.fields import RichTextUploadingField

# from markdown_deux import markdown



class PostManager(models.Manager):
    def active(self, *args, **kwargs):
        qs = self.get_queryset().filter(
            draft=False,
            publish__lte=timezone.now()
        )
        return qs


def upload_location(instance, filename):
    return "%s/%s" % (instance.id, filename)

class Category(models.Model):
    title = models.CharField(max_length=20,null=True,
                              blank=True)

    def __str__(self):
        return self.title


class Post(models.Model):

    profile = models.ForeignKey(Profile,
                                on_delete=models.CASCADE,null=True,
                              blank=True)
    title = models.CharField(max_length=250)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to=upload_location,
                              null=True,
                              blank=True,
                              width_field="width_field",
                              height_field="height_field",default='image/no_image.png')
    height_field = models.IntegerField(default=0)
    width_field = models.IntegerField(default=0)
    content = RichTextUploadingField(blank=True,null=True)
    categories = models.ManyToManyField(Category,blank=True)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)
    draft = models.BooleanField(default=False)
    publish = models.DateField(auto_now=False, auto_now_add=False)
    read_time = models.IntegerField(default=0)  # models.TimeField(null=True, blank=True) #assume minutes
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    objects = PostManager()

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title

    def total_likes(self):
        return self.likes.count()

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.id, self.slug])

    def get_api_url(self):
        return reverse("posts-api:detail", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["-timestamp", "-updated"]

    @property
    def get_content_type(self):
        instance = self
        content_type = ContentType.objects.get_for_model(instance.__class__)
        return content_type


def _generate_unique_slug(instance):
    base_slug = slugify(instance.title)
    if not base_slug:
        base_slug = "post"
    slug = base_slug
    counter = 1
    while Post.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug


@receiver(pre_save, sender=Post)
def pre_save_slug(sender, **kwargs):
    instance = kwargs["instance"]
    if not instance.slug:
        instance.slug = _generate_unique_slug(instance)


# def pre_save_post_receiver(sender, instance, *args, **kwargs):
#     if not instance.slug:
#         instance.slug = unique_slug_generator(instance)
#
#     if instance.content:
#         read_time_var = get_read_time(instance.content)
#         instance.read_time = read_time_var
#
#
# pre_save.connect(pre_save_post_receiver, sender=Post)


# for contact
