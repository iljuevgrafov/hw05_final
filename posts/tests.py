from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import Post, User, Group, Follow, Comment
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from django.core.files.base import File


class YatubeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_no_auth = Client()
        self.group = Group.objects.create(title='TestGroup', slug='TestGroup')
        self.user = User.objects.create_user(
            username="testuser", email="test@mail.com", password="12345")
        self.client.force_login(self.user)

    def test_new_profile(self):
        response = self.client.get(reverse('profile', args=[self.user]))
        self.assertEqual(response.status_code, 200)

    def test_new_post_auth(self):
        post_text = 'Test post text'
        self.client.post(reverse('new_post'), {
            'text': post_text, 'author': self.user, 'group': self.group.id})
        self.assertEqual(Post.objects.count(), 1)
        post_from_base = Post.objects.first()
        self.assertEqual(post_from_base.text, post_text)
        self.assertEqual(post_from_base.author, self.user)
        self.assertEqual(post_from_base.group, self.group)

    def test_new_post_no_auth(self):
        post_text = 'Test post text'
        response = self.client_no_auth.post(reverse('new_post'), {
                                            'text': post_text, 'author': self.user, 'group': self.group.id}, follow=True)
        self.assertEqual(Post.objects.count(), 0)
        self.assertRedirects(
            response, '/auth/login/?next=/new/')

    def find_on_pages(self, page_url, post_text, post_author, post_group):
        response = self.client.get(page_url)
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(response.context['paginator'].count, 1)
            post_on_page = response.context['page'][0]
        else:
            post_on_page = response.context['post']
        self.assertEqual(post_on_page.text, post_text)
        self.assertEqual(post_on_page.author, post_author)
        self.assertEqual(post_on_page.group, post_group)

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }
    })
    def test_new_post_on_pages(self):
        post_text = 'Test post text'
        self.post = Post.objects.create(
            text=post_text, author=self.user, group=self.group)

        page_urls = [
            reverse('profile', args=[self.user]),
            reverse('index'),
            reverse('post_view', args=[self.user, self.post.id]),
            reverse('group_posts', args=[self.group.slug])
        ]

        for page_url in page_urls:
            self.find_on_pages(page_url, self.post.text,
                               self.post.author, self.post.group)

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }
    })
    def test_post_edit(self):
        post_text = 'Test post text'
        post_new_text = 'New test post text'
        self.post = Post.objects.create(
            text=post_text, author=self.user, group=self.group)

        new_group = Group.objects.create(title='TestGroup2', slug='TestGroup2')

        self.client.post(reverse("post_edit", args=[self.user, self.post.id]), {
                         'text': post_new_text, 'group': new_group.id}, follow=True)

        page_urls = [
            reverse('profile', args=[self.user]),
            reverse('index'),
            reverse('post_view', args=[self.user, self.post.id]),
            reverse('group_posts', args=[new_group.slug])
        ]

        for page_url in page_urls:
            self.find_on_pages(page_url, post_new_text, self.user, new_group)

        response = self.client.get(
            reverse('group_posts', args=[self.group.slug]))
        self.assertEqual(response.context['paginator'].count, 0)

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }
    })
    def test_post_has_image(self):
        post_text = 'Post with image'
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        img = SimpleUploadedFile(
            'image.gif', small_gif, content_type='image/gif')

        response = self.client.post(reverse('new_post'), {
            'text': post_text, 'author': self.user, 'group': self.group.id, 'image': img}, follow=True)

        post = Post.objects.last()

        page_urls = [
            reverse('profile', args=[self.user]),
            reverse('index'),
            reverse('post_view', args=[self.user, post.id]),
            reverse('group_posts', args=[self.group.slug])
        ]

        for page_url in page_urls:
            response = self.client.get(page_url)
            self.assertContains(response, '<img', status_code=200, count=1,
                                msg_prefix='Тэг не найден на главной странице', html=False)

    def test_post_not_image(self):
        post_text = 'Post with image'
        img = SimpleUploadedFile(
            'image.gif', b"some content", content_type='image/gif')
        response = self.client.post(reverse('new_post'), {
                                    'text': post_text, 'author': self.user, 'group': self.group.id, 'image': img}, follow=True)
        self.assertFormError(response, 'form', 'image', [
                             'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'])

    def test_follow(self):
        user2 = User.objects.create_user(
            username="testuser2", email="test2@mail.com", password="12345")
        self.client.post(
            reverse('profile_follow', args=[user2.username]), follow=True)
        follow_obj = Follow.objects.filter(user=self.user, author=user2)
        self.assertEqual(follow_obj.count(), 1)
        self.assertEqual(follow_obj[0].user, self.user)
        self.assertEqual(follow_obj[0].author, user2)

    def test_unfollow(self):
        user2 = User.objects.create_user(
            username="testuser2", email="test2@mail.com", password="12345")
        Follow.objects.create(user=self.user, author=user2)
        self.client.post(
            reverse('profile_unfollow', args=[user2.username]), follow=True)
        follow_obj = Follow.objects.filter(
            user=self.user, author=user2)
        self.assertEqual(follow_obj.count(), 0)

    def test_follower_has_new_post(self):
        user_w_posts = User.objects.create_user(
            username="user_w_posts", email="user_w_posts@mail.com", password="12345")
        self.client.post(
            reverse('profile_follow', args=[user_w_posts.username]), follow=True)
        post = Post.objects.create(
            text='some text', author=user_w_posts, group=self.group)
        self.find_on_pages(reverse('follow_index'),
                           post.text, post.author, post.group)

    def test_not_follower_has_not_new_post(self):
        user_w_posts = User.objects.create_user(
            username="user_w_posts", email="user_w_posts@mail.com", password="12345")

        post = Post.objects.create(
            text='some text', author=user_w_posts, group=self.group)

        self.assertEqual(False, Follow.objects.filter(
            user=self.user, author=user_w_posts).exists())

        response = self.client.get(reverse('follow_index'))
        self.assertNotIn(post, response.context['page'])

    def test_comment_auth(self):
        second_user = User.objects.create_user(
            username="second_user", email="second_user@mail.com", password="12345")
        post = Post.objects.create(
            text='some text', author=second_user, group=self.group)
        comment_text = 'comment1'

        self.client.post(reverse(
            'add_comment', args=[second_user.username, post.id]), {'text': comment_text})
        self.assertEqual(Comment.objects.all().count(), 1)

    def test_comment_notauth(self):
        second_user = User.objects.create_user(
            username="second_user", email="second_user@mail.com", password="12345")
        post = Post.objects.create(
            text='some text', author=second_user, group=self.group)
        comment_text = 'comment1'

        self.client.post(reverse(
            'add_comment', args=[second_user.username, post.id]), {'text': comment_text})
        response = self.client_no_auth.post(reverse(
            'add_comment', args=[second_user.username, post.id]), {'text': comment_text}, follow=True)
        self.assertEqual(Comment.objects.all().count(), 1)
        self.assertRedirects(response, '/auth/login/?next=' + reverse(
            'add_comment', args=[second_user.username, post.id]))

    def test_page_cached(self):
        post_text = 'Test post text'
        post_new_text = 'Test post new text'
        self.post = Post.objects.create(
            text=post_text, author=self.user, group=self.group)
        response = self.client.get('/')
        post1 = response.context.get('page')[0]
        self.client.post(reverse("post_edit", args=[self.user, self.post.id]), {
            'text': post_new_text, 'group': self.group.id}, follow=True)
        response = self.client.get('/')
        post2 = response.context.get('page')[0]
        self.assertEqual(post1.text, post2.text)
