from django.shortcuts import render, get_object_or_404
from .models import Group, Post, Follow
from django.views.generic import CreateView
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
       )


def posts_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.grposts.all()[:12]
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group,
                                          "posts": posts,
                                          "paginator": paginator,
                                          "page": page})


class NewPost(CreateView):
    form_class = PostForm
    success_url = reverse_lazy("new_post")
    template_name = "new.html"


@login_required()
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


def thankyou(request):
    return render(request, 'thankyou.html')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.author_posts.all()
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
            user=User.objects.get(
                username=request.user
                ),
                author=User.objects.get(
                    username=username
                    )
                    ).exists():
            following = True
    return render(request, 'profile.html', {'author': author,
                                            'paginator': paginator,
                                            'following': following,
                                            'post': post,
                                            'page': page})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    comments = post.comment.all()
    return render(request, 'post.html', {
                                        'author': author,
                                        'form': form,
                                        'items': comments,
                                        'post': post})


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != profile:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect(
            "post",
            username=request.user.username,
            post_id=post_id)

    return render(
        request, 'post_new.html', {'form': form, 'post': post},)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "follow.html",
        {'post': posts, 'page': page, 'paginator': paginator}
        )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username=username)
