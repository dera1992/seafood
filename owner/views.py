# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from account.models import Profile
from foodCreate.models import Products
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404,HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from owner.models import Affiliate
from .forms import InformationForm
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.template.loader import get_template
import random

@login_required
def my_cart(request):
    myab_list = Products.objects.filter(shop__owner=request.user)
    profile = Profile.objects.filter(user=request.user).first()
    ads = Products.objects.filter(is_active=True)
    lates = Products.objects.all().order_by('-created_date')[:3]
    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))

    paginator = Paginator(myab_list, 6)  # Show 25 contacts per page
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        myab = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        myab = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        myab = paginator.page(paginator.num_pages)
    return render(request, 'owner/cart.html', {'myab': myab, 'profile': profile, 'ads': ads, 'lates': lates,
                                                 'counts': counts, 'page_request_var': page_request_var})



def bookmarked(request):
    return render(request, 'owner/bookmarked.html', {})

@login_required
def delete_post(request,pk=None):
    ad = Products.objects.get(id=pk)
    if request.user != ad.shop.owner:
        raise Http404()
    ad.is_active = False
    ad.save()
    messages.success(request, "You property has been successfuly deleted")
    return redirect('home:allads_list')


@login_required
def hide_post(request,pk=None):
    ad = Products.objects.get(id=pk)
    if request.user != ad.shop.owner:
        raise Http404()
    ad.is_active = False
    ad.save()
    messages.success(request, "You property has been successfuly deleted")
    return redirect('home:allads_list')

def create_contact(request):
    if request.POST:
        form = InformationForm(request.POST)
        if form.is_valid():
            post_info = form.save(commit=False)
            # post.user = request.user
            post = form.cleaned_data
            subject = post['subject']
            message ='Hello "{}" sent you a message below through Bunchfood contact form \n{}'.format( post['name'], post['message'])
            to_email = ['ezechdr16@gmail.com']
            from_email = post['email']
            email = EmailMessage(
                subject, message, from_email=from_email, to=to_email
            )
            email.send()
            post_info.save()

            # text = form.cleaned_data['headline','content']
            messages.add_message(request, messages.SUCCESS, 'Your message has been recieved')
            form = InformationForm()
            return redirect('owner:create_contact')

    else:
        form = InformationForm()

        args = {'form': form}
        return render(request, 'owner/others/contact.html', args)

def about_us(request):
    affiliates = Affiliate.objects.all()[:10]
    return render(request, 'owner/others/about.html', {'affiliates':affiliates})

def faq(request):
    return render(request, 'owner/others/faq.html', )


def success(request):
    return render(request, 'paystack/success-page.html',)

def failure(request):
    return render(request, 'paystack/failed-page.html',)
