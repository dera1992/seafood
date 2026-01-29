# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from blog.models import Post

from django.db import models

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post,on_delete=models.CASCADE, null=True,blank=True)
    reply = models.ForeignKey('Comment', null=True,blank=True,on_delete=models.CASCADE,related_name="replies")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return str(self.user)

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return reverse("comments:thread", kwargs={"id": self.id})
