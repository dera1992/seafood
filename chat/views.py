from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from account.models import Shop, User
from foodCreate.models import Products
from .models import Message

# Create your views here.


@login_required
def inbox(request):
    messages = (
        Message.objects.select_related("shop", "sender", "receiver", "product")
        .filter(Q(sender=request.user) | Q(receiver=request.user))
        .order_by("-timestamp")
    )

    conversations = []
    seen = set()
    for message in messages:
        other_user = message.receiver if message.sender == request.user else message.sender
        key = (message.shop_id, other_user.id)
        if key in seen:
            continue
        seen.add(key)
        unread_count = Message.objects.filter(
            shop=message.shop,
            sender=other_user,
            receiver=request.user,
            is_read=False,
        ).count()
        conversations.append(
            {
                "shop": message.shop,
                "other_user": other_user,
                "last_message": message,
                "unread_count": unread_count,
            }
        )
    return render(
        request,
        "chat/inbox.html",
        {"conversations": conversations},
    )


@login_required
def thread(request, shop_id, user_id):
    shop = get_object_or_404(Shop, id=shop_id)
    other_user = get_object_or_404(User, id=user_id)
    if shop.owner not in {request.user, other_user}:
        return HttpResponseBadRequest("Invalid conversation.")

    messages = (
        Message.objects.select_related("shop", "sender", "receiver", "product")
        .filter(shop=shop)
        .filter(sender__in=[request.user, other_user], receiver__in=[request.user, other_user])
        .order_by("timestamp")
    )
    last_message_id = messages.last().id if messages.exists() else ""
    Message.objects.filter(
        receiver=request.user,
        sender=other_user,
        shop=shop,
        is_read=False,
    ).update(is_read=True)
    products = Products.objects.filter(shop=shop).order_by("title")
    return render(
        request,
        "chat/thread.html",
        {
            "shop": shop,
            "other_user": other_user,
            "messages": messages,
            "last_message_id": last_message_id,
            "products": products,
        },
    )


@login_required
def thread_messages(request, shop_id, user_id):
    shop = get_object_or_404(Shop, id=shop_id)
    other_user = get_object_or_404(User, id=user_id)
    if shop.owner not in {request.user, other_user}:
        return HttpResponseBadRequest("Invalid conversation.")
    after_id = request.GET.get("after")
    queryset = (
        Message.objects.select_related("sender", "product")
        .filter(shop=shop)
        .filter(sender__in=[request.user, other_user], receiver__in=[request.user, other_user])
        .order_by("timestamp")
    )
    if after_id:
        queryset = queryset.filter(id__gt=after_id)
    messages = [
        {
            "id": message.id,
            "sender": message.sender.email,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "product": message.product.title if message.product else None,
        }
        for message in queryset
    ]
    return JsonResponse({"messages": messages})


@login_required
def send_message(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method.")
    receiver_id = request.POST.get("receiver_id")
    shop_id = request.POST.get("shop_id")
    product_id = request.POST.get("product_id")
    content = request.POST.get("content")
    if not receiver_id or not shop_id or not content:
        return HttpResponseBadRequest("Missing required fields.")
    receiver = get_object_or_404(User, id=receiver_id)
    shop = get_object_or_404(Shop, id=shop_id)
    product = None
    if product_id:
        product = get_object_or_404(Products, id=product_id, shop=shop)
    Message.objects.create(
        shop=shop,
        product=product,
        sender=request.user,
        receiver=receiver,
        content=content,
    )
    return redirect("chat:thread", shop_id=shop.id, user_id=receiver.id)
