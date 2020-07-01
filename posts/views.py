from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
from django.core.cache.backends import locmem


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


# @cache_page(60 * 15)
def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect(post_view, username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(post_view, username=username, post_id=post_id)
    return render(request, 'new_post.html', {'edit': True, 'form': form, 'post': post})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    if request.user.is_authenticated == True:
        following = Follow.objects.filter(
            user=request.user, author=user).first()
    else:
        following = None

    paginator = Paginator(posts, 5)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'profile.html', {'page': page, 'paginator': paginator, 'author': user, 'following': following})


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    count = user.posts.all().count
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm()
    items = Comment.objects.filter(post=post_id)
    return render(request, 'post.html', {'author': user, 'post': post, 'count': count, 'form': form, 'items': items})


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect(post_view, username=username, post_id=post_id)
    return redirect(post_view, username=username, post_id=post_id)


@login_required
def follow_index(request):

    posts = Post.objects.select_related('author').filter(
        author__following__user=request.user)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_exist = Follow.objects.filter(user=request.user, author=author).first()

    if not is_exist and author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect(profile, username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(profile, username)
