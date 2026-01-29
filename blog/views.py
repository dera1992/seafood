from owner.models import Affiliate

try:
    from urllib import quote_plus  # python 2
except:
    pass

try:
    from urllib.parse import quote_plus  # python 3
except:
    pass

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count
from foodCreate.models import Products

from comments.forms import CommentForm
from comments.models import  Comment
from .forms import PostForm
from .models import Post,Category
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from account.models import Profile


def get_category_count():
    queryset = Post \
        .objects \
        .values('categories__title') \
        .annotate(Count('categories__title'))
    return queryset

@login_required
def post_create(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404

    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        instance.profile = profile
        instance.save()
        # message success
        messages.success(request, "Successfully Created")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "blog/post_form.html", context)

def post_detail(request, id, slug):
    category_count = get_category_count()
    post = get_object_or_404(Post, id=id, slug=slug)
    comments = Comment.objects.filter(post=post, reply=None).order_by('-id')
    most_recent = Post.objects.order_by('-timestamp')[:3]
    lates = Products.objects.order_by('-created_date')[:5]
    affiliates = Affiliate.objects.all()[:10]
    is_liked = False
    if request.user.is_authenticated and post.likes.filter(id=request.user.id).exists():
        is_liked = True

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        comment_form = CommentForm(request.POST or None)
        if comment_form.is_valid():
            content = request.POST.get('content')
            reply_id = request.POST.get('comment_id')
            comment_qs = None
            if reply_id:
                comment_qs = Comment.objects.get(id=reply_id)
            comment = Comment.objects.create(post=post, user=request.user, content=content, reply=comment_qs)
            comment.save()
            # return HttpResponseRedirect(post.get_absolute_url())
    else:
        comment_form= CommentForm()

    context = {
        'instance': post,
        'is_liked': is_liked,
        'total_likes': post.total_likes(),
        'comments': comments,
        'comment_form': comment_form,
        'category_count': category_count,
        'most_recent': most_recent,
        'lates':lates,
        'affiliates': affiliates
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('blog/comments.html', context, request=request)
        return JsonResponse({'form': html})

    return render(request, 'blog/blog_detail.html', context)

def post_list(request):
    category_count = get_category_count()
    today = timezone.now().date()
    queryset_list = Post.objects.active()  # .order_by("-timestamp")
    most_recent = Post.objects.order_by('-timestamp')[:3]
    affiliates = Affiliate.objects.all()[:10]
    if request.user.is_staff or request.user.is_superuser:
        queryset_list = Post.objects.all()

    query = request.GET.get("q")
    if query:
        queryset_list = queryset_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        ).distinct()
    paginator = Paginator(queryset_list, 8)  # Show 25 contacts per page
    page_request_var = "page"
    page = request.GET.get(page_request_var)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)

    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))
    lates = Products.objects.order_by('-created_date')[:5]
    context = {
        "object_list": queryset,
        "title": "List",
        "page_request_var": page_request_var,
        "today": today,
        'counts': counts,
        'lates': lates,
        'category_count': category_count,
        'most_recent': most_recent,
        'affiliates':affiliates
    }
    return render(request, "blog/blog_list.html", context)

@login_required
def post_update(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request, "<a href='#'>Item</a> Saved", extra_tags='html_safe')
        return HttpResponseRedirect(instance.get_absolute_url())

    context = {
        "title": instance.title,
        "instance": instance,
        "form": form,
    }
    return render(request, "blog/post_form.html", context)

@login_required
def post_delete(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    instance.delete()
    messages.success(request, "Successfully deleted")
    return redirect("posts:list")

# for contact


