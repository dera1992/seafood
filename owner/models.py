from django.db import models

# Create your models here.
class Information (models.Model):
    name = models.CharField(max_length=300,blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    pub_date = models.DateField(auto_now_add=True)
    email = models.EmailField(max_length=200)

    def __str__(self):
        return self.subject


class Affiliate (models.Model):
    name = models.CharField(max_length=300,blank=True, null=True)
    iframe = models.TextField(max_length=5000,blank=True, null=True)
    created = models.DateField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return self.name