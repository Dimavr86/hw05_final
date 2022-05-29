from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse 

from yatube.settings import POSTS_ON_PAGE

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


class PostList(ListView):
    paginate_by = POSTS_ON_PAGE


class IndexView(PostList):
    model = Post
    template_name = 'posts/index.html'


class GroupView(PostList):
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        posts = Post.objects.filter(group__slug=self.kwargs['slug'])
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, slug=self.kwargs['slug'])
        return context


class ProfileView(PostList):
    template_name = 'posts/profile.html'

    def get_queryset(self):
        posts = Post.objects.filter(author__username=self.kwargs['username'])
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = User.objects.get(username=self.kwargs['username'])
        following = self.request.user.is_authenticated
        if following:
            following = context['author'].following.filter(user=self.request.user).exists()
        context['following'] = following
        return context


class PostDetalView(FormMixin, DetailView):
    model = Post
    form_class = CommentForm
    template_name = 'posts/post_detail.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'posts/create_post.html'
    form_class = PostForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('posts:profile', kwargs={'username': self.request.user})


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    extra_context = {'is_edit': True}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != self.request.user:
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        self.object.save()
        return HttpResponseRedirect(reverse(
            'posts:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
            )
        )


class FollowIndexView(LoginRequiredMixin, PostList):
    template_name = 'posts/follow.html'
    extra_context = {'follow': True}

    def get_queryset(self):
        posts_list = Post.objects.filter(author__following__user=self.request.user)
        return posts_list


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if not Follow.objects.filter(
        author=author,
        user=user
    ).exists() and user != author:
        new_follow = Follow(author=author, user=user)
        new_follow.save()
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    follow = Follow.objects.get(
        author=author,
        user=user
    )
    if follow:
        follow.delete()
        return redirect('posts:profile', username=username)
