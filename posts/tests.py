from django.test import TestCase, Client
from django.urls import reverse
from .models import Post, User, Group, Follow, Comment
from django.core.cache import cache


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

    def test_new_post_on_pages(self):
        cache.clear()
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

    def test_post_edit(self):
        cache.clear()
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

    def test_post_has_image(self):
        cache.clear()
        post_text = 'Post with image'
        with open('media/posts/lev2.jpeg', 'rb') as img:
            response = self.client.post(reverse('new_post'), {
                'text': post_text, 'author': self.user, 'group': self.group.id, 'image': img}, follow=True)
        self.post = Post.objects.last()

        page_urls = [
            reverse('profile', args=[self.user]),
            reverse('index'),
            reverse('post_view', args=[self.user, self.post.id]),
            reverse('group_posts', args=[self.group.slug])
        ]

        for page_url in page_urls:
            response = self.client.get(page_url)
            self.assertContains(response, '<img', status_code=200, count=1,
                                msg_prefix='Тэг не найден на главной странице', html=False)

    def test_post_not_image(self):
        post_text = 'Post with image'
        with open('media/posts/tests.py', 'rb') as img:
            response = self.client.post(reverse('new_post'), {
                'text': post_text, 'author': self.user, 'group': self.group.id, 'image': img}, follow=True)
        self.assertFormError(response, 'form', 'image', [
                             'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'])

    def test_follow_unfollow(self):
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@mail.com", password="12345")
        self.client.post(
            reverse('profile_follow', args=[self.user2.username]), follow=True)
        follow_obj = Follow.objects.filter(
            user=self.user, author=self.user2).last()
        self.assertIsNotNone(follow_obj)

        self.client.post(
            reverse('profile_unfollow', args=[self.user2.username]), follow=True)
        follow_obj = Follow.objects.filter(
            user=self.user, author=self.user2).last()
        self.assertIsNone(follow_obj)

    def test_new_post_in_follow(self):
        self.user_w_posts = User.objects.create_user(
            username="user_w_posts", email="user_w_posts@mail.com", password="12345")
        self.second_user = User.objects.create_user(
            username="second_user", email="second_user@mail.com", password="12345")
        self.client.post(
            reverse('profile_follow', args=[self.user_w_posts.username]), follow=True)
        post = Post.objects.create(
            text='some text', author=self.user_w_posts, group=self.group)
        response = self.client.get(reverse('follow_index'))
        self.assertIn(post, response.context['page'])

        self.client.force_login(self.second_user)
        response = self.client.get(reverse('follow_index'))
        self.assertNotIn(post, response.context['page'])

    def test_comment_notauth(self):
        self.second_user = User.objects.create_user(
            username="second_user", email="second_user@mail.com", password="12345")
        post = Post.objects.create(
            text='some text', author=self.second_user, group=self.group)
        comment_text = 'comment1'

        self.client.post(reverse(
            'add_comment', args=[self.second_user.username, post.id]), {'text': comment_text})
        self.assertEqual(Comment.objects.all().count(), 1)

        response = self.client_no_auth.post(reverse(
            'add_comment', args=[self.second_user.username, post.id]), {'text': comment_text}, follow=True)
        self.assertEqual(Comment.objects.all().count(), 1)
        self.assertRedirects(response, '/auth/login/?next=' + reverse(
            'add_comment', args=[self.second_user.username, post.id]))
