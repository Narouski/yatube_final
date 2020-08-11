from django.test import TestCase
from .models import Group, Post, Follow
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404


class Test(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        self.client.force_login(self.user)
        self.anon_client = Client()

    def test_create_posts(self):
        post = Post.objects.create(
            text='text',
            author=self.user,
            grposts=self.group)
        for url in (
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse(
                "post",
                kwargs={"username": self.user.username, "post_id": post.id})):
            response = self.client.get(url)
            self.client.post(
                reverse('new_post'),
                data={'text': 'test', 'group': self.group.id})
            self.assertEqual(response, post.text)
            self.assertContains(response, post.author)

    def test_post_on_page(self, url, post):
        """To test that post from arguments is on pages"""
        response = self.auth_client.get(url)
        if 'paginator' in response.context:
            posts_list = response.context['paginator'].object_list
            self.assertEqual(len(posts_list), 1)
            self.assertEqual(posts_list[0], post)
        else:
            self.assertEqual(response.context['post'], post)

    def test_post_on_pages(self):
        """To test that created post is on pages"""
        post = Post.objects.create(
            text='test text',
            group=self.group,
            author=self.user)
        urls = self.get_urls(post=post)
        for url in urls:
            self.check_post_on_page(url=url, post=post)

    def test_post_edit(self):
        """To test if author can edit post and post is on pages"""
        post = Post.objects.create(
            text='test text',
            group=self.group,
            author=self.user)
        edit_group = Group.objects.create(
            title='edit_group',
            slug='edit_group')
        response = self.auth_client.post(
            reverse('post_edit', kwargs={
                'username': post.author.username,
                'post_id': post.id}),
            {'text': 'edit text', 'group': edit_group.id}, follow=True)
        post = Post.objects.get(id=post.id)
        urls = self.get_urls(post=post)
        for url in urls:
            self.check_post_on_page(url=url, post=post)
        response = self.auth_client.get(reverse('group_posts',
                                        kwargs={'slug': self.group.slug}))
        self.assertNotIn(post, response.context['paginator'].object_list)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_add_image(self):
        text = 'post with file not image'
        file_mock = mock.MagicMock(spec=File, name='copy.txt')
        response = self.client_auth.post(reverse('new_post'), data={
            'author': self.user,
            'group': self.group.pk,
            'text': text,
            'image': file_mock
            })
        self.assertFormError(response,
                             form='form',
                             field='image',
                             errors='Загрузите правильное изображение.'
                                ' Файл, который вы загрузили,'
                                ' поврежден или не является изображением.')

    def test_follow_add_and_delete(self, username):
        before = Follow.objects.all().count()
        self.client_auth_follower.get(
            reverse(
                "profile_follow",
                kwargs={
                    "username": self.user_following.username,
                },
            )
        )
        after = Follow.objects.all().count()
        following = False
        self.assertEqual(before + 1, after)
        if Follow.objects.filter(
            user=User.objects.get(
                username=self.user_follower.username),
                author=User.objects.get(
                    username=self.user_following.username)).count() != 0:
            following = True
            self.client_auth_follower.get(
                reverse(
                        "profile_unfollow",
                        kwargs={
                        "username": self.user_following.username,
                        },
                )
            )
            after = Follow.objects.all().count()
            self.assertEqual(0, after)

    def test_cache(self):
        self.client_auth.post(reverse('new_post'),
                              data={'text': 'text',
                                    'group': self.group.id,
                                    'author': self.user},
                              follow=True)
        posts_new = Post.objects.all()
        self.assertEqual(posts_new.first().text, 'text')
        response = self.client_auth.get(reverse('index'))
        text = Post.objects.filter(text='text')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, text)
