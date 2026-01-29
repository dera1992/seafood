from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from account.models import Shop, User
from .models import Message

# Create your views here.


@login_required
def inbox(request):
    messages = (
        Message.objects.select_related("shop", "sender", "receiver")
        .filter(receiver=request.user)
        .order_by("-timestamp")
    )
    return render(request, "chat/inbox.html", {"messages": messages})


@login_required
def send_message(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method.")
    receiver_id = request.POST.get("receiver_id")
    shop_id = request.POST.get("shop_id")
    content = request.POST.get("content")
    if not receiver_id or not shop_id or not content:
        return HttpResponseBadRequest("Missing required fields.")
    receiver = get_object_or_404(User, id=receiver_id)
    shop = get_object_or_404(Shop, id=shop_id)
    Message.objects.create(
        shop=shop,
        sender=request.user,
        receiver=receiver,
        content=content,
    )
    return redirect("chat:inbox")
